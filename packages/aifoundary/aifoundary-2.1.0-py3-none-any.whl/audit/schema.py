from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class KnowledgeAccess(BaseModel):
    allowed_sources: List[str]
    denied_sources: List[str]
    retrieved_docs_hash: str

class ActionAuthorization(BaseModel):
    agent_id: str
    action: str
    resource: str
    decision: str
    policy: str
    confidence: float

class DecisionEvidence(BaseModel):
    decision_id: str
    timestamp: datetime
    policy_version: str
    input_hash: str
    integrity_hash: str

class AuditReport(BaseModel):
    summary: str
    knowledge_access: KnowledgeAccess
    action_authorization: ActionAuthorization
    decision_evidence: DecisionEvidence
    compliance_mapping: Dict[str, List[str]]
