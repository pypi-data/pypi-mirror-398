import sys
from audit.generator import generate_from_uaal
from audit.pdf import generate_pdf

def main():
    if len(sys.argv) < 2:
        print("Usage: aifoundry-audit <decision_id>")
        sys.exit(1)

    decision_id = sys.argv[1]

    # Demo inputs (v1)
    rag_policy = {
        "allow_sources": ["internal_docs"],
        "deny_sources": ["web"]
    }

    action = {
        "agent_id": "pricing-agent",
        "action": "update_price",
        "resource": "sku:123",
        "context": {"confidence": 0.82}
    }

    mcp_result = {
        "decision": "allowed",
        "policy": "pricing_limit"
    }

    report = generate_from_uaal(
        decision_id,
        rag_policy,
        action,
        mcp_result
    )

    # JSON output (auditors)
    print(report.model_dump_json(indent=2))

    # PDF output (execs / regulators)
    generate_pdf(report)
    print("PDF written to audit_report.pdf")

if __name__ == "__main__":
    main()
