from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from pydantic import ConfigDict


class MCPAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    agent_id: str = Field(..., alias="agent")
    action: str
    resource: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    knowledge_hash: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def require_hash_for_legacy_agent(cls, values):
        # Legacy path uses `agent` → provenance required
        if "agent" in values and "agent_id" not in values:
            if not values.get("knowledge_hash"):
                raise Exception("knowledge_hash is required for MCPAction")
        return values
