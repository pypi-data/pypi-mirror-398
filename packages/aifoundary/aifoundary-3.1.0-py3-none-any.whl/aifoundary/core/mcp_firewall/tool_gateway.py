from aifoundary.core.mcp_firewall.schemas.action import MCPAction
from aifoundary.core.uaal.record import record_decision

class ToolExecutionError(Exception):
    pass

def execute_tool(
    *,
    action_dict: dict,
    tool_fn,
    policy_name: str,
    parent_decision_id: str | None = None,
):
    action = MCPAction(**action_dict)

    if not action.knowledge_hash:
        raise ToolExecutionError("knowledge_hash required")

    # Tool runs ONLY after UAAL approval
    decision_id = record_decision(
        agent_id=action.agent_id,
        action=action.action,
        policy=policy_name,
        outcome="allowed",
        knowledge_hash=action.knowledge_hash,
        parent_decision_id=parent_decision_id,
    )

    tool_fn()
    return decision_id
