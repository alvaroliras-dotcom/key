"""
Añade al PDF de peticiones de Nuria una página «hecho / descartado / pendiente» por versión
(instrucción de Nuria, 4 oct 2026: el PDF es el registro de versiones de La Llave).

Uso:
    python docs/pagina_version.py docs/version-v2.json

El JSON lleva: version, fecha, resumen, hecho[], descartado[], pendiente[], cifras[] y pie.
Cada elemento de hecho/descartado/pendiente es [titulo, detalle].
Necesita: pip install reportlab pypdf
"""

import io
import json
import os
import sys

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Frame, Paragraph, Spacer, Table, TableStyle

AQUI = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(AQUI, "la-llave-peticiones-de-mejora-nuria.pdf")
FUCSIA = HexColor("#E0007A")
GRIS = HexColor("#6B6B6B")
NEGRO = HexColor("#151515")
COLORES = {"hecho": HexColor("#1E8E5A"), "descartado": HexColor("#8A8A8A"), "pendiente": HexColor("#C98A00")}


def _fuentes():
    ruta = "C:/Windows/Fonts"
    try:
        pdfmetrics.registerFont(TTFont("Arial", os.path.join(ruta, "arial.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-Bold", os.path.join(ruta, "arialbd.ttf")))
        return "Arial", "Arial-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def pagina(datos: dict) -> bytes:
    normal, negrita = _fuentes()
    def st(**k):
        base = {"fontName": normal, "fontSize": 8.6, "leading": 11.2, "textColor": NEGRO}
        return ParagraphStyle("x", **(base | k))
    s_cab = st(textColor=GRIS, fontSize=7.5)
    s_tit = ParagraphStyle("t", fontName=negrita, fontSize=20, leading=23, textColor=NEGRO)
    s_sub = st(fontSize=9.5, leading=13, textColor=GRIS)
    s_sec = ParagraphStyle("s", fontName=negrita, fontSize=10.5, leading=14, textColor=FUCSIA)
    s_item = st()
    s_pie = st(fontSize=7, leading=9, textColor=GRIS)

    flujo = [
        Paragraph(f"LA LLAVE · REGISTRO DE VERSIONES · {datos['fecha'].upper()}", s_cab),
        Spacer(1, 8),
        Paragraph(f"Versión {datos['version']}: hecho, descartado y pendiente", s_tit),
        Spacer(1, 6),
        Paragraph(datos["resumen"], s_sub),
        Spacer(1, 10),
    ]
    if datos.get("cifras"):
        celdas = [[Paragraph(f"<font name='{negrita}' size='15' color='#E0007A'>{v}</font><br/>{t}", s_item)
                   for v, t in datos["cifras"]]]
        tabla = Table(celdas, colWidths=[(A4[0] - 100) / len(datos["cifras"])] * len(datos["cifras"]))
        tabla.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("LINEABOVE", (0, 0), (-1, 0), 0.6, FUCSIA),
                                   ("TOPPADDING", (0, 0), (-1, -1), 6)]))
        flujo += [tabla, Spacer(1, 10)]

    for clave_sec, titulo in (("hecho", "Hecho"), ("descartado", "Descartado y por qué"), ("pendiente", "Pendiente")):
        flujo.append(Paragraph(f"<font color='{COLORES[clave_sec].hexval().replace('0x', '#')}'>■</font> {titulo}", s_sec))
        flujo.append(Spacer(1, 3))
        for t, d in datos[clave_sec]:
            flujo.append(Paragraph(f"<font name='{negrita}'>{t}.</font> {d}", s_item))
            flujo.append(Spacer(1, 2.5))
        flujo.append(Spacer(1, 7))
    flujo.append(Paragraph(datos["pie"], s_pie))

    buf = io.BytesIO()
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFillColor(FUCSIA)
    c.rect(0, A4[1] - 6, A4[0], 6, stroke=0, fill=1)
    Frame(50, 40, A4[0] - 100, A4[1] - 80, showBoundary=0).addFromList(flujo, c)
    c.setFont(normal, 7.5)
    c.setFillColor(GRIS)
    c.drawRightString(A4[0] - 50, 24, f"El Gordo y el Flaco Marketing Online · La Llave {datos['version']}")
    c.save()
    return buf.getvalue()


def main(ruta_json: str):
    with open(ruta_json, encoding="utf-8") as f:
        datos = json.load(f)
    lector = PdfReader(PDF)
    escritor = PdfWriter()
    for p in lector.pages:
        escritor.add_page(p)
    for p in PdfReader(io.BytesIO(pagina(datos))).pages:
        escritor.add_page(p)
    with open(PDF, "wb") as f:
        escritor.write(f)
    print(f"Añadida la página de la versión {datos['version']}: {PDF} ({len(escritor.pages)} páginas)")


if __name__ == "__main__":
    main(sys.argv[1])
