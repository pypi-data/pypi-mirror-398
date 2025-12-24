from uaal_core import record_decision

# v1: simulate lookup (later replace with real storage)
def fetch_decision(decision_id: str) -> dict:
    # In v2 this queries DB / chain / log
    return {
        "decision_id": decision_id,
        "policy_version": "v1",
        "timestamp": None
    }
