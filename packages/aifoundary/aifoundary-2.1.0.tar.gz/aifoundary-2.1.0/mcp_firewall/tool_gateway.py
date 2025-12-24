from mcp_firewall.firewall import evaluate
from mcp_firewall.uaal_bridge import write_decision
from mcp_firewall.schemas.action import MCPAction

class ToolExecutionError(Exception):
    pass

def execute_tool(
    action_dict: dict,
    policy_path: str,
    tool_fn
):
    """
    The ONLY allowed way to execute tools.
    """
    action = MCPAction(**action_dict)

    result = evaluate(action, policy_path)

    if result["decision"] != "allowed":
        raise ToolExecutionError("Action not authorized")

    write_decision(action, result)
    return tool_fn()
