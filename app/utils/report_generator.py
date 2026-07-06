from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from openpyxl import Workbook


def generate_pdf(complaints):

    buffer = BytesIO()

    pdf = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph(
        "<b>College Complaint Report</b>",
        styles["Heading1"]
    )

    elements.append(title)

    data = [
        [
            "ID",
            "Student",
            "Category",
            "Title",
            "Status",
            "Date"
        ]
    ]

    for complaint in complaints:

        data.append([
            complaint.id,
            complaint.student.name,
            complaint.category.category_name,
            complaint.title,
            complaint.status,
            complaint.created_at.strftime("%d-%m-%Y")
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 1, colors.black),

        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

    ]))

    elements.append(table)

    pdf.build(elements)

    buffer.seek(0)

    return buffer


def generate_excel(complaints):

    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Complaints"

    sheet.append([
        "ID",
        "Student",
        "Category",
        "Title",
        "Status",
        "Date"
    ])

    for complaint in complaints:

        sheet.append([
            complaint.id,
            complaint.student.name,
            complaint.category.category_name,
            complaint.title,
            complaint.status,
            complaint.created_at.strftime("%d-%m-%Y")
        ])

    buffer = BytesIO()

    workbook.save(buffer)

    buffer.seek(0)

    return buffer