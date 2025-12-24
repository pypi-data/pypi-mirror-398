import json
import hashlib
from pathlib import Path
from datetime import datetime

AUDIT_CHAIN_FILE = Path("aifoundary_audit.chain")
GENESIS_HASH = hashlib.sha256(b"GENESIS").hexdigest()


def _canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def emit_audit_event(event: dict):
    if AUDIT_CHAIN_FILE.exists():
        prev = json.loads(AUDIT_CHAIN_FILE.read_text().splitlines()[-1])["event_hash"]
    else:
        prev = GENESIS_HASH

    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **event,
        "prev_hash": prev,
    }

    record["event_hash"] = hashlib.sha256(
        (prev + _canonical(record)).encode()
    ).hexdigest()

    with AUDIT_CHAIN_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")

    return record


def verify_chain():
    if not AUDIT_CHAIN_FILE.exists():
        return True, "No audit chain found"

    prev = GENESIS_HASH

    for i, line in enumerate(AUDIT_CHAIN_FILE.read_text().splitlines()):
        evt = json.loads(line)
        unsigned = {k: v for k, v in evt.items() if k != "event_hash"}

        expected = hashlib.sha256(
            (prev + _canonical(unsigned)).encode()
        ).hexdigest()

        if evt["event_hash"] != expected:
            return False, f"Tamper detected at line {i+1}"

        prev = evt["event_hash"]

    return True, "Audit chain verified"
