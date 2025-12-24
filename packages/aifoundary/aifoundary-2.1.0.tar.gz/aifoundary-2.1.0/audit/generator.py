import hashlib
from datetime import datetime
from audit.schema import AuditReport, KnowledgeAccess, ActionAuthorization, DecisionEvidence

def generate_audit_report(
    decision_id: str,
    rag_policy: dict,
    action: dict,
    mcp_result: dict
) -> AuditReport:

    retrieved_docs_hash = hashlib.sha256(
        str(rag_policy).encode()
    ).hexdigest()

    input_hash = hashlib.sha256(
        str(action).encode()
    ).hexdigest()

    integrity_hash = hashlib.sha256(
        f"{decision_id}{input_hash}".encode()
    ).hexdigest()

    report = AuditReport(
        summary=(
            f"Action '{action['action']}' by agent '{action['agent_id']}' "
            f"was {mcp_result['decision']} under policy '{mcp_result.get('policy')}'."
        ),
        knowledge_access=KnowledgeAccess(
            allowed_sources=rag_policy.get("allow_sources", []),
            denied_sources=rag_policy.get("deny_sources", []),
            retrieved_docs_hash=retrieved_docs_hash
        ),
        action_authorization=ActionAuthorization(
            agent_id=action["agent_id"],
            action=action["action"],
            resource=action["resource"],
            decision=mcp_result["decision"],
            policy=mcp_result.get("policy", "none"),
            confidence=action["context"].get("confidence", 0.0)
        ),
        decision_evidence=DecisionEvidence(
            decision_id=decision_id,
            timestamp=datetime.utcnow(),
            policy_version="v1",
            input_hash=input_hash,
            integrity_hash=integrity_hash
        ),
        compliance_mapping={}
    )

    return report

from audit.compliance import compliance_mapping

def generate_audit_report_with_compliance(
    decision_id: str,
    rag_policy: dict,
    action: dict,
    mcp_result: dict
):
    report = generate_audit_report(
        decision_id, rag_policy, action, mcp_result
    )
    report.compliance_mapping = compliance_mapping()
    return report

from audit.uaal_reader import fetch_decision

def generate_from_uaal(
    decision_id: str,
    rag_policy: dict,
    action: dict,
    mcp_result: dict
):
    decision = fetch_decision(decision_id)
    report = generate_audit_report_with_compliance(
        decision_id, rag_policy, action, mcp_result
    )
    report.decision_evidence.policy_version = decision["policy_version"]
    return report
