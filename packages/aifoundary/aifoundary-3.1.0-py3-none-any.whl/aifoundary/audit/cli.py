import json
import sys
from pathlib import Path
from aifoundary.audit.export import build_audit_graph
from aifoundary.audit.pdf import write_pdf

def main():
    if len(sys.argv) != 2:
        print("Usage: aifoundry-audit <decision_id>")
        sys.exit(1)

    decision_id = sys.argv[1]

    audit = build_audit_graph(decision_id)

    json_path = Path(f"audit_{decision_id}.json")
    pdf_path = Path(f"audit_{decision_id}.pdf")

    json_path.write_text(json.dumps(audit, indent=2))
    write_pdf(audit, pdf_path)

    print(f"✔ Audit JSON: {json_path}")
    print(f"✔ Audit PDF:  {pdf_path}")
