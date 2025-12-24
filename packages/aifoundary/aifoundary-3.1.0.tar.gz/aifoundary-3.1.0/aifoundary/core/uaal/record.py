import uuid
from typing import Optional
from aifoundary.core.uaal.decision_store_sqlite import (
    DecisionRecord,
    save_decision,
    get_decision,
    compute_decision_hash
)

def record_decision(
    agent_id: str,
    action: str,
    policy: str,
    outcome: str,
    knowledge_hash: str,
    parent_decision_id: Optional[str] = None
) -> str:
    if not knowledge_hash:
        raise ValueError("knowledge_hash is required")

    decision_id = f"dec-{uuid.uuid4().hex[:8]}"

    parent_hash = ""
    if parent_decision_id:
        parent = get_decision(parent_decision_id)
        parent_hash = parent.decision_hash

    decision_hash = compute_decision_hash(
        decision_id,
        agent_id,
        action,
        policy,
        outcome,
        knowledge_hash,
        parent_hash
    )

    record = DecisionRecord(
        decision_id=decision_id,
        agent_id=agent_id,
        action=action,
        policy=policy,
        outcome=outcome,
        knowledge_hash=knowledge_hash,
        parent_decision_id=parent_decision_id,
        decision_hash=decision_hash
    )

    save_decision(record)
    return decision_id
