from typing import Dict
from .decision_graph import DecisionNode

_DECISIONS: Dict[str, DecisionNode] = {}

def store_decision(node: DecisionNode):
    _DECISIONS[node.decision_id] = node

def get_decision(decision_id: str) -> DecisionNode:
    return _DECISIONS[decision_id]

def get_full_lineage(decision_id: str):
    lineage = []
    current = _DECISIONS.get(decision_id)

    while current:
        lineage.append(current)
        current = _DECISIONS.get(current.parent_decision_id)

    return list(reversed(lineage))
