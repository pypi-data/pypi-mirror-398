from typing import Dict, Any, List
from aifoundary.core.uaal.decision_store_sqlite import get_full_lineage

def build_audit_graph(decision_id: str) -> Dict[str, Any]:
    lineage = get_full_lineage(decision_id)

    nodes = []
    for d in lineage:
        nodes.append({
            "decision_id": d.decision_id,
            "agent_id": d.agent_id,
            "action": d.action,
            "policy": d.policy,
            "outcome": d.outcome,
            "knowledge_hash": d.knowledge_hash,
            "parent_decision_id": d.parent_decision_id,
            "decision_hash": d.decision_hash,
        })

    return {
        "root_decision_id": lineage[0].decision_id,
        "node_count": len(nodes),
        "audit_graph": nodes,
        "integrity": {
            "tamper_evident": True,
            "hash_algorithm": "SHA-256",
            "chained": True
        }
    }
