from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf(report, path="audit_report.pdf"):
    c = canvas.Canvas(path, pagesize=A4)
    text = c.beginText(40, 800)

    text.textLine("AI DECISION AUDIT REPORT")
    text.textLine("")
    text.textLine(report.summary)
    text.textLine("")
    text.textLine("Knowledge Access:")
    text.textLine(f" Allowed: {report.knowledge_access.allowed_sources}")
    text.textLine(f" Denied: {report.knowledge_access.denied_sources}")
    text.textLine("")
    text.textLine("Action Authorization:")
    text.textLine(f" Action: {report.action_authorization.action}")
    text.textLine(f" Decision: {report.action_authorization.decision}")
    text.textLine(f" Policy: {report.action_authorization.policy}")
    text.textLine("")
    text.textLine("Decision Evidence:")
    text.textLine(f" Decision ID: {report.decision_evidence.decision_id}")
    text.textLine(f" Integrity Hash: {report.decision_evidence.integrity_hash}")

    c.drawText(text)
    c.showPage()
    c.save()
