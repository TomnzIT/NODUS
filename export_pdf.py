from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from datetime import datetime
import io

def generate_pdf(summary, coverage):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    style_title = styles["Heading1"]
    style_subtitle = styles["Heading2"]
    style_normal = styles["BodyText"]
    style_bold = ParagraphStyle(name='Bold', parent=style_normal, fontName='Helvetica-Bold')

    story = []

    story.append(Paragraph("Cybersecurity Mapping Report", style_title))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", style_normal))
    story.append(Spacer(1, 12))

    story.append(Paragraph("📊 Coverage Summary", style_subtitle))
    story.append(Paragraph(f"<b>Total coverage:</b> {round(coverage, 2)}%", style_normal))
    story.append(Spacer(1, 12))

    story.append(Paragraph("📁 Category Breakdown", style_subtitle))

    summary_sorted = summary.fillna(0).sort_values(by="Coverage %", ascending=False)

    data = [["Category", "Coverage %", "Full Match", "Partial Match", "No Match", "Total"]]
    for _, row in summary_sorted.iterrows():
        cat = str(row.get("control_category", "Unknown"))
        coverage_pct = round(float(row.get("Coverage %", 0)), 1)
        full = int(row.get("Full Match", 0))
        partial = int(row.get("Partial Match", 0))
        none = int(row.get("No Match", 0))
        total = int(row.get("Total", 0))
        data.append([cat, f"{coverage_pct}%", full, partial, none, total])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))

    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer