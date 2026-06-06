from reportlab.pdfgen import canvas

def generate_report(df, risk, intersections, colocation):

    file = "report.pdf"
    c = canvas.Canvas(file)

    c.drawString(50, 800, "Tower Dump Forensic Report")

    y = 770

    c.drawString(50, y, f"Total Records: {len(df)}")
    y -= 20

    c.drawString(50, y, "Risk Scores:")
    y -= 20

    for k, v in risk.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 15

    c.save()

    return file