import sys
import json
import yaml

from aifoundary.core.mcp_firewall.schemas.action import MCPAction
from aifoundary.core.uaal import record_decision

def main():
    if len(sys.argv) != 3:
        print("Usage: mcp-check action.json policy.yaml")
        sys.exit(1)

    action_file, policy_file = sys.argv[1], sys.argv[2]

    with open(action_file) as f:
        action_data = json.load(f)

    with open(policy_file) as f:
        policy = yaml.safe_load(f)

    action = MCPAction(**action_data)

    decision = (
        "allowed"
        if action.confidence >= policy["min_confidence"]
        else "denied"
    )

    record = record_decision(
        agent_id=action.agent,
        action=action.action,
        decision=decision,
        policy=policy["name"],
        confidence=action.confidence,
        knowledge_hash=action.knowledge_hash,
    )

    print({
        "decision": decision,
        "policy": policy["name"],
        "decision_id": record["decision_id"],
        "knowledge_hash": action.knowledge_hash,
    })

if __name__ == "__main__":
    main()
