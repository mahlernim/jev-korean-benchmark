from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SEED = 20260917
PRICE = 0.042 / 1_000_000
ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    # Order matters for the option-order experiment. Never sort mapping keys here.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def filehash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def frozen(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise ValueError(f"Frozen file differs: {path.name}; create a new experiment")
    else:
        write_new(path, value)


def load_manifest(path):
    value = read(path)
    expected = value.pop("sha256")
    if digest(value) != expected:
        raise ValueError("Manifest integrity failure")
    value["sha256"] = expected
    ids = [e["eval_id"] for e in value["evaluations"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evaluation IDs")
    for e in value["evaluations"]:
        if digest(e["request"]) != e["request_hash"]:
            raise ValueError("Request integrity failure")
        if e["kind"] == "choice" and e["gold"] not in e["request"]["questions"]["answer"]["criteria"]:
            raise ValueError("Invalid gold mapping")
    return value
