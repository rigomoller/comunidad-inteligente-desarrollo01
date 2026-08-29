from io import BytesIO

import qrcode
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas


NAVY = HexColor("#102B49")
GOLD = HexColor("#F2AF21")
INK = HexColor("#172438")
MUTED = HexColor("#5F6F80")
LIGHT = HexColor("#F4F6F8")


def _wrapped_text(pdf, text, x, y, width, font="Helvetica", size=11, leading=16):
    pdf.setFont(font, size)
    for line in simpleSplit(text, font, size, width):
        pdf.drawString(x, y, line)
        y -= leading
    return y


def build_residence_certificate_pdf(certificate, verification_url):
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    pdf.setTitle(f"Certificado de residencia {certificate.certificate_number}")
    pdf.setAuthor(certificate.neighborhood.name)
    pdf.setSubject("Certificado de residencia verificable")
    page_width, page_height = A4
    margin = 52

    pdf.setFillColor(NAVY)
    pdf.rect(0, page_height - 132, page_width, 132, stroke=0, fill=1)
    pdf.setFillColor(GOLD)
    pdf.rect(0, page_height - 138, page_width, 6, stroke=0, fill=1)
    pdf.setFillColor(HexColor("#FFFFFF"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin, page_height - 48, certificate.neighborhood.name.upper())
    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawString(margin, page_height - 84, "CERTIFICADO DE RESIDENCIA")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, page_height - 106, f"Folio {certificate.certificate_number}")

    y = page_height - 184
    pdf.setFillColor(INK)
    pdf.setFont("Helvetica", 11)
    introduction = (
        f"La directiva de {certificate.neighborhood.name}, en uso de la facultad otorgada "
        "por la Ley N.° 20.718, certifica que la persona individualizada a continuación "
        "declaró residir en el domicilio indicado y presentó antecedentes de respaldo, "
        "los cuales fueron revisados por una persona autorizada de la organización."
    )
    y = _wrapped_text(pdf, introduction, margin, y, page_width - 2 * margin, size=11, leading=17)

    y -= 18
    box_height = 176
    pdf.setFillColor(LIGHT)
    pdf.roundRect(margin, y - box_height, page_width - 2 * margin, box_height, 12, stroke=0, fill=1)
    pdf.setFillColor(INK)
    details = [
        ("Nombre", certificate.applicant_name),
        ("RUT", certificate.rut),
        ("Domicilio", certificate.address),
        ("Comuna", certificate.commune),
        ("Finalidad declarada", certificate.purpose),
        ("Fecha de emisión", certificate.issued_at.astimezone().strftime("%d-%m-%Y")),
    ]
    detail_y = y - 28
    for label, value in details:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.setFillColor(MUTED)
        pdf.drawString(margin + 20, detail_y, label.upper())
        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(INK)
        detail_y = _wrapped_text(pdf, str(value), margin + 142, detail_y, page_width - 2 * margin - 170, size=11, leading=14)
        detail_y -= 10

    y -= box_height + 28
    warning = (
        "La persona solicitante declaró bajo juramento que los antecedentes proporcionados "
        "son verdaderos. Faltar a la verdad puede generar las sanciones señaladas en el "
        "artículo 212 del Código Penal."
    )
    pdf.setFillColor(HexColor("#FFF4CF"))
    pdf.roundRect(margin, y - 64, page_width - 2 * margin, 64, 10, stroke=0, fill=1)
    pdf.setFillColor(INK)
    _wrapped_text(pdf, warning, margin + 18, y - 20, page_width - 2 * margin - 36, size=9.5, leading=13)

    y -= 112
    reviewer = certificate.reviewed_by.get_full_name() or certificate.reviewed_by.username
    pdf.setStrokeColor(MUTED)
    pdf.line(margin, y, margin + 210, y)
    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y - 17, reviewer)
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(MUTED)
    pdf.drawString(margin, y - 31, "Directiva autorizada")

    qr_image = qrcode.make(verification_url)
    qr_buffer = BytesIO()
    qr_image.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_size = 92
    qr_x = page_width - margin - qr_size
    qr_y = y - 55
    pdf.drawImage(ImageReader(qr_buffer), qr_x, qr_y, qr_size, qr_size, mask="auto")
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawCentredString(qr_x + qr_size / 2, qr_y - 10, "Escanear para verificar")

    pdf.setStrokeColor(GOLD)
    pdf.line(margin, 54, page_width - margin, 54)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 7.5)
    footer = f"Código de verificación: {certificate.verification_code}"
    pdf.drawString(margin, 40, footer)
    pdf.drawRightString(page_width - margin, 40, "Documento electrónico verificable")

    pdf.showPage()
    pdf.save()
    output.seek(0)
    return output
