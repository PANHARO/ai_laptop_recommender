"""Local staging, review audit and crash-recoverable multi-CSV transactions."""
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from contextlib import contextmanager
from filelock import FileLock

from .models import now

CANONICAL = ('laptops', 'offers', 'source_checks', 'issues')


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.staging = self.root / 'staging'
        self.staging.mkdir(exist_ok=True)
        self.lock = FileLock(str(self.staging / 'review.lock'), timeout=15)
        self.database = self.staging / 'collection.sqlite3'
        with self.lock, self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS candidates (
                    candidate_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'pending', revision INTEGER NOT NULL DEFAULT 0,
                    edited TEXT, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    event_id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL,
                    action TEXT NOT NULL, payload TEXT NOT NULL, reviewed_at TEXT NOT NULL
                );
            ''')
        self.recover()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA busy_timeout=15000')
        db.execute('PRAGMA synchronous=FULL')
        try:
            with db:
                yield db
        finally:
            db.close()

    def add(self, candidate):
        with self.lock, self.connect() as db:
            result = db.execute('INSERT OR IGNORE INTO candidates(candidate_id,payload,updated_at) VALUES(?,?,?)',
                (candidate['candidate_id'], json.dumps(candidate, ensure_ascii=False), now()))
            return result.rowcount == 1

    def get(self, candidate_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM candidates WHERE candidate_id=?', (candidate_id,)).fetchone()
        if row is None:
            raise KeyError('Candidate not found')
        result = json.loads(row['payload'])
        result.update(state=row['state'], revision=row['revision'], original_fields=result['fields'].copy())
        if row['edited']:
            result['fields'] = json.loads(row['edited'])
        return result

    def list(self):
        with self.connect() as db:
            ids = [row[0] for row in db.execute('SELECT candidate_id FROM candidates ORDER BY rowid')]
        return [self.get(i) for i in ids]

    def receipt(self, event_id):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM reviews WHERE event_id=?', (event_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def reviews(self, candidate_id):
        with self.connect() as db:
            rows = db.execute('SELECT payload FROM reviews WHERE candidate_id=? ORDER BY rowid', (candidate_id,))
            return [json.loads(r[0]) for r in rows]

    def canonical(self):
        output = {}
        with self.lock:
            for name in CANONICAL:
                with (self.root/'data'/f'{name}.csv').open(encoding='utf-8-sig', newline='') as f:
                    output[name] = list(csv.DictReader(f))
        return output

    def commit(self, event, tables):
        """Caller holds lock. Write intent before any canonical CSV is replaced."""
        changes = {}
        schema = json.loads((self.root/'config/schema.json').read_text())
        for name in CANONICAL if tables is not None else ():
            path = self.root/'data'/f'{name}.csv'
            old = path.read_bytes()
            output = io.StringIO(newline='')
            writer = csv.DictWriter(output, fieldnames=[f['name'] for f in schema[name]['fields']], lineterminator='\n')
            writer.writeheader(); writer.writerows(tables[name])
            new = output.getvalue().encode('utf-8')
            if old != new:
                changes[name] = dict(before=base64.b64encode(old).decode(), after=base64.b64encode(new).decode())
        intent = dict(event=event, files=changes)
        directory = self.staging/'transactions'/event['event_id']
        directory.mkdir(parents=True, exist_ok=True)
        atomic_bytes(directory/'intent.json', json_bytes(intent))
        atomic_bytes(self.staging/'pending_transaction.json', json_bytes(intent))
        self._finish(intent)

    def _finish(self, intent):
        # Detect outside/manual writes rather than replaying over unrelated new data.
        for name, values in intent['files'].items():
            if name not in CANONICAL:
                raise RuntimeError('Unexpected file in transaction; recovery stopped.')
            path = self.root/'data'/f'{name}.csv'
            if path.read_bytes() not in (base64.b64decode(values['before']), base64.b64decode(values['after'])):
                raise RuntimeError(f'{name}.csv changed outside the pending transaction. Restore/resolve it before recovery; no overwrite performed.')
        for name, values in intent['files'].items():
            atomic_bytes(self.root/'data'/f'{name}.csv', base64.b64decode(values['after']))
        event = intent['event']
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM reviews WHERE event_id=?', (event['event_id'],)).fetchone():
                db.execute('INSERT INTO reviews VALUES(?,?,?,?,?)', (event['event_id'], event['candidate_id'], event['action'], json.dumps(event, ensure_ascii=False), event['reviewed_at']))
                db.execute('UPDATE candidates SET state=?,revision=revision+1,edited=?,updated_at=? WHERE candidate_id=?',
                    (event['state'], json.dumps(event['fields'], ensure_ascii=False), event['reviewed_at'], event['candidate_id']))
        atomic_bytes(self.staging/'transactions'/event['event_id']/'complete.json', json_bytes(dict(completed_at=now())))
        (self.staging/'pending_transaction.json').unlink(missing_ok=True)

    def recover(self):
        with self.lock:
            path = self.staging/'pending_transaction.json'
            if path.exists():
                self._finish(json.loads(path.read_text(encoding='utf-8')))
