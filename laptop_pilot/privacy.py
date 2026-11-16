"""Reject staged human records, even when force-added past .gitignore."""
import csv
import io
from pathlib import PurePosixPath
import subprocess


def blocked_blob(path, content):
    name = PurePosixPath(path).name.lower()
    parts = [part.lower() for part in PurePosixPath(path).parts]
    if any(part in ("private", "pilot_private", "consent_admin") for part in parts):
        return True
    if name.startswith("itm360_laptop_pilot") or name in (
        "pilot_profiles.csv", "pilot_judgments.csv", "students.json", "ratings.json",
        "split_manifest.json", "student_metrics.json", "held_out_predictions.json",
    ) or name.endswith((".joblib", ".keras")):
        return True
    if name.endswith(".csv"):
        try:
            reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
            fields = set(reader.fieldnames or [])
            human_fields = fields & {"participant_id", "response_code", "student_id", "consent_status"}
            # Empty canonical CSV templates are permitted. Human rows are not.
            if human_fields and next(reader, None) is not None:
                return True
        except (UnicodeError, csv.Error):
            return name in ("students.csv", "ratings.csv", "assignments.csv")
    return False


def guard_index():
    result = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
                            check=True, capture_output=True)
    blocked = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        blob = subprocess.run(["git", "show", ":" + path], check=True, capture_output=True).stdout
        if blocked_blob(path, blob):
            blocked.append(path)
    if blocked:
        raise ValueError("Participant data/model artifacts must remain local; unstage: " + ", ".join(blocked))
    return True
