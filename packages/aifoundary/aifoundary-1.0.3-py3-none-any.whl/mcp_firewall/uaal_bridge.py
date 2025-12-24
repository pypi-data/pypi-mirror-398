try:
    from uaal_core import record_decision
except ImportError:
    def record_decision(**kwargs):
        return "uaal-not-installed"

def write_decision(action, result):
    return record_decision(
        agent_id=action.agent_id,
        action=action.action,
        resource=action.resource,
        outcome=result["decision"],
        metadata={
            "inputs": action.inputs,
            "context": action.context,
            "policy": result.get("policy"),
            "source": "mcp-firewall"
        }
    )
