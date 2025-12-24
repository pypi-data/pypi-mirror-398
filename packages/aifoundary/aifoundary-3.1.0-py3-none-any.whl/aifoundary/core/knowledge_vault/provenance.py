import hashlib
import json
from typing import List, Dict

def hash_knowledge(docs: List[Dict]) -> str:
    """
    Deterministic hash of knowledge used by an AI agent.
    Stored in UAAL for audit provenance.
    """
    payload = json.dumps(docs, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
