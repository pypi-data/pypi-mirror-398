from aifoundary.core.uaal.record import record_decision

def write_decision(action, result):
    record = record_decision(
        agent_id=action.agent_id,
        action=action.action,
        decision=result["decision"],
        policy=result["policy"],
        confidence=action.confidence,
        knowledge_hash=action.knowledge_hash,
    )
    return record["decision_id"]
