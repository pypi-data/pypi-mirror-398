from .policy import load_policy
from .schemas.action import MCPAction

def evaluate(action: MCPAction, policy_path: str) -> dict:
    policy = load_policy(policy_path)

    for rule in policy.get("policies", []):
        if rule["match"]["action"] != action.action:
            continue

        conditions = rule.get("allow_if", [])
        for cond in conditions:
            if "confidence" in cond:
                threshold = float(cond.split(">=")[1])
                if action.context.get("confidence", 0) < threshold:
                    return {"decision": "denied", "policy": rule["name"]}

        return {"decision": "allowed", "policy": rule["name"]}

    return {"decision": "denied", "reason": "no_matching_policy"}
