"""Generate sample credit card invoice PDFs for testing."""
from datetime import date
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def _br(value: Decimal) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def generate_inter_pdf(output_path: str) -> None:
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18,
                                  textColor=colors.HexColor("#FF6A00"))
    normal = styles["Normal"]
    right = ParagraphStyle("Right", parent=normal, alignment=TA_RIGHT)
    center = ParagraphStyle("Center", parent=normal, alignment=TA_CENTER)

    elements.append(Paragraph("BANCO INTER S.A.", title_style))
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("Fatura do Cartão de Crédito", styles["Heading2"]))
    elements.append(Spacer(1, 4*mm))

    info_data = [
        ["Cartão Final:", "3456"],
        ["Cliente:", "LUCAS HENRIQUE DUTRA"],
        ["Fechamento:", "15/06/2026"],
        ["Vencimento:", "05/07/2026"],
        ["Valor Total:", _br(Decimal("3245.60"))],
    ]
    info_table = Table(info_data, colWidths=[120, 200])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTWEIGHT", (0, 0), (0, -1), "bold"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    elements.append(Paragraph("Lançamentos", styles["Heading3"]))
    elements.append(Spacer(1, 3*mm))

    txns = [
        ["02/05/2026", "IFOOD PEDIDO 1234", _br(Decimal("45.90"))],
        ["05/05/2026", "UBER *VIAGEM ABC", _br(Decimal("32.50"))],
        ["08/05/2026", "NETFLIX.COM", _br(Decimal("45.90"))],
        ["10/05/2026", "DROGARIA SAO PAULO", _br(Decimal("89.30"))],
        ["12/05/2026", "SHOPEE COMPRA 9012 (1/3)", _br(Decimal("199.99"))],
        ["12/05/2026", "SHOPEE COMPRA 9012 (2/3)", _br(Decimal("199.99"))],
        ["12/05/2026", "SHOPEE COMPRA 9012 (3/3)", _br(Decimal("199.99"))],
        ["15/05/2026", "RESTAURANTE BOM SABOR", _br(Decimal("124.50"))],
        ["18/05/2026", "SPOTIFY PREMIUM", _br(Decimal("21.90"))],
        ["20/05/2026", "UBER *VIAGEM DEF", _br(Decimal("18.75"))],
        ["22/05/2026", "CINEMA SHOPPING", _br(Decimal("56.00"))],
        ["25/05/2026", "AMAZON BR 7890 (1/2)", _br(Decimal("349.90"))],
        ["25/05/2026", "AMAZON BR 7890 (2/2)", _br(Decimal("349.90"))],
        ["28/05/2026", "CURSO ONLINE UDEMY", _br(Decimal("29.90"))],
        ["30/05/2026", "MERCADO LIVRE 5678", _br(Decimal("178.50"))],
        ["30/05/2026", "ESTORNO MERCADO LIVRE", _br(Decimal("-178.50"))],
    ]

    header = ["Data", "Descrição", "Valor"]
    data = [header] + txns

    col_widths = [65, 280, 80]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF6A00")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    t.setStyle(TableStyle(style_commands))
    elements.append(t)
    elements.append(Spacer(1, 6*mm))

    fee_data = [
        ["IOF", _br(Decimal("3.45"))],
        ["Encargos Financeiros", _br(Decimal("12.50"))],
    ]
    fee_table = Table(fee_data, colWidths=[200, 80])
    fee_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("Encargos", styles["Heading3"]))
    elements.append(fee_table)

    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(width="100%", color=colors.grey))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(
        f"Total da Fatura: {_br(Decimal('3245.60'))}",
        ParagraphStyle("Total", parent=right, fontSize=14, fontName="Helvetica-Bold")
    ))

    doc.build(elements)
    print(f"Inter PDF generated: {output_path}")


def generate_nubank_pdf(output_path: str) -> None:
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18,
                                  textColor=colors.HexColor("#8A05BE"))
    normal = styles["Normal"]
    right = ParagraphStyle("Right", parent=normal, alignment=TA_RIGHT)

    elements.append(Paragraph("Nubank", title_style))
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("Fatura do Cartão de Crédito", styles["Heading2"]))
    elements.append(Spacer(1, 4*mm))

    info_data = [
        ["Cartão Final:", "9012"],
        ["Cliente:", "LUCAS H DUTRA"],
        ["Vencimento:", "10/07/2026"],
        ["Valor Total:", _br(Decimal("1857.30"))],
    ]
    info_table = Table(info_data, colWidths=[120, 200])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTWEIGHT", (0, 0), (0, -1), "bold"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    elements.append(Paragraph("Lançamentos", styles["Heading3"]))
    elements.append(Spacer(1, 3*mm))

    txns = [
        ["01/06/2026", "IFOOD PEDIDO 5678", _br(Decimal("35.90"))],
        ["03/06/2026", "UBER *VIAGEM GHI", _br(Decimal("27.50"))],
        ["05/06/2026", "NETFLIX.COM", _br(Decimal("45.90"))],
        ["08/06/2026", "DROGARIA SAO PAULO", _br(Decimal("65.30"))],
        ["10/06/2026", "SHOPEE COMPRA 3456 (1/2)", _br(Decimal("299.99"))],
        ["10/06/2026", "SHOPEE COMPRA 3456 (2/2)", _br(Decimal("299.99"))],
        ["12/06/2026", "PIZZARIA DO BAIRRO", _br(Decimal("89.50"))],
        ["15/06/2026", "SPOTIFY PREMIUM", _br(Decimal("21.90"))],
        ["18/06/2026", "AMAZON BR 1234", _br(Decimal("529.90"))],
        ["20/06/2026", "Uber *VIAGEM JKL", _br(Decimal("15.75"))],
        ["25/06/2026", "CINEMA SHOPPING", _br(Decimal("42.00"))],
        ["28/06/2026", "MERCADO LIVRE 9012", _br(Decimal("183.67"))],
    ]

    header = ["Data", "Descrição", "Valor"]
    data = [header] + txns

    col_widths = [65, 280, 80]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8A05BE")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    t.setStyle(TableStyle(style_commands))
    elements.append(t)

    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(width="100%", color=colors.grey))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(
        f"Total da Fatura: {_br(Decimal('1857.30'))}",
        ParagraphStyle("Total", parent=right, fontSize=14, fontName="Helvetica-Bold")
    ))

    doc.build(elements)
    print(f"Nubank PDF generated: {output_path}")


if __name__ == "__main__":
    generate_inter_pdf("test_fatura_inter.pdf")
    generate_nubank_pdf("test_fatura_nubank.pdf")
