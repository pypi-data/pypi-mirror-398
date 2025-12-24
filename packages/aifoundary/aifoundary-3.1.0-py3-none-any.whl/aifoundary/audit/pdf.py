from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pathlib import Path

def write_pdf(audit_data: dict, out_path: Path):
    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "AI Decision Audit Report")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Root Decision ID: {audit_data['root_decision_id']}")
    y -= 20
    c.drawString(40, y, f"Decisions in Chain: {audit_data['node_count']}")
    y -= 30

    for node in audit_data["audit_graph"]:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, f"Decision: {node['decision_id']}")
        y -= 14

        c.setFont("Helvetica", 9)
        for k, v in node.items():
            c.drawString(60, y, f"{k}: {v}")
            y -= 12
            if y < 60:
                c.showPage()
                y = height - 40

        y -= 10

    c.save()
