import yaml

def load_rag_policy(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def filter_context(context: list, policy_path: str) -> list:
    """
    Enforces RAG governance by filtering knowledge context
    based on allowed / denied sources.
    """
    policy = load_rag_policy(policy_path)

    allowed = set(policy.get("allow_sources", []))
    denied = set(policy.get("deny_sources", []))

    filtered = []
    for item in context:
        source = item.get("source")

        if source in denied:
            continue

        if allowed and source not in allowed:
            continue

        filtered.append(item)

    return filtered
