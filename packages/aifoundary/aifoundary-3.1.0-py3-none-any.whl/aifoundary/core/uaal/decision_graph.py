from dataclasses import dataclass, field
from typing import Optional, Dict
import hashlib
import json
from datetime import datetime

@dataclass
class DecisionNode:
    decision_id: str
    agent_id: str
    action: str
    policy: str
    outcome: str
    knowledge_hash: str
    parent_decision_id: Optional[str] = None
    parent_hash: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    integrity_hash: str = field(init=False)

    def __post_init__(self):
        payload = {
            "decision_id": self.decision_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "policy": self.policy,
            "outcome": self.outcome,
            "knowledge_hash": self.knowledge_hash,
            "parent_hash": self.parent_hash,
            "timestamp": self.timestamp,
        }
        self.integrity_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
