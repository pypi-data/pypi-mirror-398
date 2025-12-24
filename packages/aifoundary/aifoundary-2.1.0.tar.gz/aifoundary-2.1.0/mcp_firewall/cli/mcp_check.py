import json
import sys
from mcp_firewall.schemas.action import MCPAction
from mcp_firewall.firewall import evaluate
from mcp_firewall.uaal_bridge import write_decision

def main():
    if len(sys.argv) < 3:
        print("Usage: mcp-check action.json policy.yaml")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        action = MCPAction(**json.load(f))

    result = evaluate(action, sys.argv[2])
    decision_id = write_decision(action, result)

    print({
        "decision": result["decision"],
        "policy": result.get("policy"),
        "decision_id": decision_id
    })

if __name__ == "__main__":
    main()
