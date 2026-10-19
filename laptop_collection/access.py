"""Public HTML access with robots checks, bounded retries and no protection bypass."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit, urljoin, unquote

from bs4 import BeautifulSoup
import requests

from .models import allowed_url


class AccessBlocked(RuntimeError):
    pass


class RetrievalError(RuntimeError):
    pass


def robots_allowed(text, url, agent):
    """RFC-style groups, longest matching rule, wildcard and end-anchor support."""
    groups, agents, rules, reading_rules = [], [], [], False
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if ':' not in line:
            continue
        key, value = [x.strip() for x in line.split(':', 1)]
        if key.lower() == 'user-agent':
            if reading_rules:
                groups.append((agents, rules)); agents, rules, reading_rules = [], [], False
            agents.append(value.lower())
        elif key.lower() in ('allow', 'disallow') and agents:
            reading_rules = True
            if value:
                rules.append((key.lower(), value))
    groups.append((agents, rules))
    selected, specificity = [], -1
    for names, group_rules in groups:
        score = max([0 if x == '*' else len(x) for x in names if x == '*' or x in agent.lower()] or [-1])
        if score < 0:
            continue
        if score > specificity:
            selected, specificity = group_rules[:], score
        elif score == specificity:
            selected.extend(group_rules)
    p = urlsplit(url)
    target = unquote(p.path or '/') + ('?' + unquote(p.query) if p.query else '')
    matches = []
    for kind, path in selected:
        ending = path.endswith('$')
        path = unquote(path[:-1] if ending else path)
        pattern = '^' + re.escape(path).replace(r'\*', '.*') + ('$' if ending else '')
        if re.search(pattern, target):
            matches.append((len(path.replace('*', '')), kind == 'allow'))
    return max(matches)[1] if matches else True


def robot_delay(text, agent):
    # Honor any applicable published delay, conservatively including wildcard groups.
    delays, names, reading_rules = [], [], False
    for line in text.splitlines():
        line = line.split('#', 1)[0]
        key, sep, value = line.partition(':')
        if key.strip().lower() == 'user-agent':
            if reading_rules:
                names, reading_rules = [], False
            names.append(value.strip().lower())
            continue
        if not sep or not names:
            continue
        reading_rules = True
        if key.strip().lower() == 'crawl-delay' and any(x == '*' or x in agent.lower() for x in names):
            try:
                delay = float(value.strip())
                if 0 <= delay <= 86400:
                    delays.append(delay)
                elif delay > 86400:
                    raise AccessBlocked('Published crawl delay is too large for this run; use manual import.')
            except ValueError:
                pass
    return max(delays or [0])


def policy_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
        tag.decompose()
    return (soup.select_one('#content') or soup.find('main') or soup).get_text(' ', strip=True)


def prohibited_terms(text):
    words = r'(?:scrap\w*|crawl\w*|robots?|automated\s+(?:access|retrieval|collection|tools|means|processes)|data\s+mining)'
    denial = r'(?:prohibit\w*|forbid\w*|not\s+(?:permitted|allowed|to)|may\s+not|must\s+not|do\s+not|\bno\b)'
    return bool(re.search(words + r'.{0,120}' + denial + '|' + denial + r'.{0,120}' + words, text, re.I))


class PublicClient:
    def __init__(self, source, config, log_path=None, sleep=time.sleep, session=None):
        self.source, self.config = source, config
        self.sleep, self.session = sleep, session or requests.Session()
        self.session.headers.update({'User-Agent': config['user_agent'], 'Accept': 'text/html,text/plain;q=0.9'})
        self.last_request = 0
        self.delay = max(3.0, config['delay_seconds'])
        self.robots, self.checked, self.blocked = '', False, False
        self.log_path = Path(log_path) if log_path else None
        self.audit = []

    def log(self, **entry):
        entry['timestamp'] = datetime.now(timezone.utc).isoformat()
        self.audit.append(entry)
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def _wire(self, url, policy=False):
        if self.blocked:
            raise AccessBlocked('This source is stopped for this run.')
        url = allowed_url(url, self.source)
        for redirect in range(4):
            for attempt in range(self.config['retries'] + 1):
                wait = self.delay - (time.monotonic() - self.last_request)
                if wait > 0:
                    self.sleep(wait)
                self.last_request = time.monotonic()
                try:
                    response = self.session.get(url, timeout=self.config['timeout_seconds'], allow_redirects=False, stream=True)
                except requests.RequestException as exc:
                    self.log(url=url, event='network_error', attempt=attempt, error=str(exc)[:300])
                    if attempt == self.config['retries']:
                        raise RetrievalError(str(exc)) from exc
                    self.sleep(min(2 ** attempt, 5))
                    continue
                status = response.status_code
                self.log(url=url, event='http', status=status, attempt=attempt)
                if status in (401, 403, 429):
                    response.close(); self.blocked = True
                    raise AccessBlocked(f'HTTP {status}; source stopped. Use manual URL import, not another route.')
                if 500 <= status <= 599:
                    response.close()
                    if attempt == self.config['retries']:
                        raise RetrievalError(f'HTTP {status} after bounded retries')
                    self.sleep(min(2 ** attempt, 5)); continue
                raw = bytearray()
                if status not in (301, 302, 303, 307, 308):
                    try:
                        for chunk in response.iter_content(65536):
                            raw.extend(chunk)
                            if len(raw) > self.config['max_response_bytes']:
                                raise RetrievalError('Response exceeds configured byte limit.')
                        encoding = response.encoding if response.encoding and response.encoding.lower() != 'iso-8859-1' else 'utf-8'
                        text = bytes(raw).decode(encoding, errors='replace')
                    except requests.RequestException as exc:
                        self.log(url=url, event='stream_error', attempt=attempt, error=str(exc)[:300])
                        if attempt == self.config['retries']:
                            raise RetrievalError('Response stream failed after bounded retries: ' + str(exc)) from exc
                        self.sleep(min(2 ** attempt, 5))
                        continue
                    finally:
                        response.close()
                break
            if status in (301, 302, 303, 307, 308):
                target = allowed_url(urljoin(url, response.headers.get('Location', '')), self.source)
                response.close()
                if urlsplit(target).netloc != urlsplit(url).netloc:
                    raise RetrievalError('Cross-origin redirect not followed; inspect manually and check that origin\'s policy first.')
                if (self.robots or not policy) and not robots_allowed(self.robots, target, self.config['user_agent']):
                    raise AccessBlocked('Redirect target is disallowed by robots.txt.')
                url = target
                continue
            soup = BeautifulSoup(text, 'html.parser')
            headline = ' '.join(x.get_text(' ', strip=True) for x in soup.find_all(['title', 'h1']))
            visible = soup.get_text(' ',strip=True)
            challenge = r'verify (?:you are|you.re) human|checking your browser|just a moment|access denied|unusual traffic|sign in to continue'
            if re.search(challenge + r'|captcha|authentication required|please (?:log|sign) in', headline, re.I) or (len(visible)<1500 and re.search(challenge + r'|complete the captcha',visible,re.I)):
                self.blocked = True
                raise AccessBlocked('Access challenge or sign-in wall; source stopped without attempting a bypass.')
            return dict(status=status, url=url, text=text, raw=bytes(raw), sha256=hashlib.sha256(raw).hexdigest())
        raise RetrievalError('Too many redirects.')

    def check_policy(self):
        if self.source['mode'] != 'public_html':
            raise AccessBlocked('Source configured for manual URL / authorized export import only.')
        result = self._wire(self.source['base_url'] + '/robots.txt', policy=True)
        if result['status'] == 200:
            self.robots = result['text']
        elif result['status'] == 404:
            self.log(event='robots_missing', note='404 does not grant permission; terms and path checks still apply.')
        else:
            raise AccessBlocked(f"Cannot establish robots policy: HTTP {result['status']}")
        self.delay = max(self.delay, robot_delay(self.robots, self.config['user_agent']))
        reports = [dict(kind='robots', url=result['url'], status=result['status'], sha256=result['sha256'])]
        for url in self.source['terms_urls']:
            if not robots_allowed(self.robots, url, self.config['user_agent']):
                raise AccessBlocked('Terms page disallowed by robots; inspect manually before collection.')
            terms = self._wire(url, policy=True)
            if terms['status'] != 200:
                raise AccessBlocked('Could not inspect configured access terms; use manual import.')
            text = policy_text(terms['text'])
            if prohibited_terms(text):
                self.blocked = True
                raise AccessBlocked('Possible automated-access restriction in terms; manual/authorized import only until reviewed.')
            reports.append(dict(kind='terms', url=terms['url'], status=200, text_sha256=hashlib.sha256(text.encode()).hexdigest()))
        self.checked = True
        self.log(event='policy_checked', pages=reports, note=self.source['policy_note'])
        return reports

    def get(self, url):
        if not self.checked:
            raise AccessBlocked('Check robots.txt and terms before retrieving a product or listing.')
        url = allowed_url(url, self.source)
        if not robots_allowed(self.robots, url, self.config['user_agent']):
            raise AccessBlocked('URL is disallowed by robots.txt; not retrieved.')
        result = self._wire(url)
        if result['status'] != 200:
            raise RetrievalError(f"HTTP {result['status']}: {url}")
        return result
