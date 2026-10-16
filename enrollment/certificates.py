"""Part 3 - Completion certificate as a PDF (FR-11), built with ReportLab.

ReportLab is imported inside the function on purpose: if the library is not
installed, only the certificate download fails, not the whole website.
"""
from io import BytesIO


def build_certificate_pdf(*, learner_name, module_title, completed_on, score, certificate_id):
    """Return a BytesIO containing a landscape A4 certificate PDF."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    navy = HexColor("#1f4e79")
    text = HexColor("#333333")

    buffer = BytesIO()
    width, height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    pdf.setTitle(f"Certificate - {module_title}")

    pdf.setStrokeColor(navy)
    pdf.setLineWidth(4)
    pdf.rect(30, 30, width - 60, height - 60)
    pdf.setLineWidth(1)
    pdf.rect(40, 40, width - 80, height - 80)

    pdf.setFillColor(navy)
    pdf.setFont("Helvetica-Bold", 36)
    pdf.drawCentredString(width / 2, height - 120, "Certificate of Completion")

    pdf.setFillColor(text)
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width / 2, height - 170, "This certifies that")

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 215, learner_name)

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width / 2, height - 255, "has successfully completed the training module")

    pdf.setFillColor(navy)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 295, module_title)

    pdf.setFillColor(text)
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 335, f"Assessment score: {score}/100")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(90, 90, f"Completed on: {completed_on:%d %B %Y}")
    pdf.drawRightString(width - 90, 90, f"Certificate ID: {certificate_id}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
