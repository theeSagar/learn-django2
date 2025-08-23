import io, os, uuid
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import pdfencrypt, colors
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.colors import HexColor
from rest_framework.response import Response
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import *
from userprofile.models import *
from document_center.utils import *
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch



def draw_justified_text(pdf, text, x, y, max_width, font="Helvetica", font_size=12):
    """Function to justify text in a PDF."""
    pdf.setFont(font, font_size)
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_length = pdf.stringWidth(word + " ", font, font_size)
        if current_length + word_length <= max_width:
            current_line.append(word)
            current_length += word_length
        else:
            lines.append(current_line)
            current_line = [word]
            current_length = word_length

    if current_line:
        lines.append(current_line)

    for line in lines:
        total_spacing = max_width - sum(
            pdf.stringWidth(word + " ", font, font_size) for word in line
        )
        if len(line) > 1:
            space_between_words = total_spacing / (len(line) - 1)
        else:
            space_between_words = 0  # No extra spacing needed for single-word lines

        x_pos = x
        for word in line:
            pdf.drawString(x_pos, y, word)
            x_pos += pdf.stringWidth(word + " ", font, font_size) + space_between_words

        y -= font_size + 2  # Move to next line

    return y  # Return updated y position


def draw_wrapped_text(pdf, text, x, y, max_width, font="Helvetica", font_size=12):
    """Function to wrap text properly and align it to the left."""
    pdf.setFont(font, font_size)

    # ✅ Split text into multiple lines that fit within max_width
    lines = simpleSplit(text, font, font_size, max_width)

    # ✅ Draw each line at the correct position
    for line in lines:
        pdf.drawString(x, y, line)
        y -= font_size + 2  # Move to next line with spacing

    return y  # Return updated y position


def generate_caf_pdf(
    caf,
    investment_details,
    common_applications,
    addresses,
    intention_data,
    customer_data,
):
    """Generates a dynamic PDF for CAF Investment Details, using data from multiple models."""
    caf_reference_id = str(uuid.uuid4())  # Generate a unique reference ID

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    left_margin, right_margin = 50, 50
    start_height, line_height = 800, 18
    page_width, page_height = A4
    y_position = start_height

    def check_space(height_required):
        nonlocal y_position
        if y_position - height_required < 50:
            pdf.showPage()
            add_header()
            y_position = start_height
            return True
        return False

    def add_header():
        """Adds header with MPIDC logo and title on new page."""
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawRightString(
            page_width - right_margin,
            start_height,
            "MP Industrial Development Corporation Ltd.",
        )
        pdf.setFont("Helvetica", 10)
        pdf.drawRightString(
            page_width - right_margin,
            start_height - 12,
            "21, Arera Hills, Bhopal, 462011",
        )
        pdf.setFont("Helvetica-Bold", 12)
        text = "COMMON APPLICATION FORM"
        text_width = pdf.stringWidth(text, "Helvetica", 12)
        x_start = (page_width - text_width) / 2
        y_position = start_height - 3 * line_height

        # Draw the text
        pdf.drawString(x_start, y_position, text)

        # Draw an underline
        pdf.line(x_start, y_position - 2, x_start + text_width + 3, y_position - 2)
        # pdf.drawString((page_width - text_width) / 2, start_height - 3 * line_height, text)

    # logo_url = os.path.join(settings.MEDIA_ROOT, 'MPIDC_Logo.jpg')
    # logo = ImageReader(logo_url)
    # pdf.drawImage(
    #     logo,
    #     left_margin,
    #     y_position - line_height - 60,
    #     width=150,
    #     height=150,
    #     mask="auto",
    # )
    logo_height = 0.8 * inch
    logo_width = 2.0 * inch

    logo_url = os.path.join(settings.MEDIA_ROOT, 'MPIDC_Logo.jpg')
    logo = ImageReader(logo_url)
    pdf.drawImage(
        logo,
        left_margin,
        y_position - line_height - logo_height,  
        width=logo_width,
        height=logo_height,
        mask='auto'
    )

    add_header()
    y_position -= 5 * line_height

    pdf.setFont("Helvetica-Bold", 10)
    application_text = f"Intention Number.: {safe_str(intention_data.intention_id)}"
    date_text = f"Date: {datetime.now().strftime('%d/%m/%Y')}"
    date_text_width = pdf.stringWidth(date_text, "Helvetica-Bold", 12)
    right_position = page_width - right_margin - date_text_width

    pdf.drawString(left_margin, y_position, application_text)
    pdf.drawString(right_position, y_position, date_text)
    y_position -= 2 * line_height

    check_space(5 * line_height)
    pdf.setFont("Helvetica", 12)

    def draw_wrapped_text(text, max_width=475):
        """Draw wrapped text dynamically, adjusting for new pages."""
        nonlocal y_position
        words = text.split()
        line = ""
        pdf.setFont("Helvetica", 11)
        for word in words:
            if pdf.stringWidth(line + word, "Helvetica", 10) < max_width:
                line += word + " "
            else:
                check_space(line_height)
                pdf.drawString(left_margin, y_position, line.strip())
                y_position -= line_height
                line = word + " "
        check_space(line_height)
        pdf.drawString(left_margin, y_position, line.strip())
        y_position -= line_height

    blue_row_data = [["Project Details"]]
    blue_row_table = Table(blue_row_data, colWidths=[500])
    blue_row_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1669ae")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    blue_row_table.wrapOn(pdf, left_margin, y_position)
    blue_row_table.drawOn(pdf, left_margin, y_position - (1 * 5))
    y_position -= (2 * 8) + 15

    table_data = []

    if investment_details.type_of_investment:
        table_data.append(
            ["Type of Unit", safe_str(investment_details.type_of_investment)]
        )

    if investment_details.project_name:
        table_data.append(
            ["Project Title", Paragraph(safe_str(investment_details.project_name))]
        )

    if intention_data.product_name:
        table_data.append(
            ["Product Title", Paragraph(safe_str(intention_data.product_name))]
        )

    if intention_data.activity:
        table_data.append(
            ["Activity Type", Paragraph(safe_str(intention_data.activity))]
        )
    if investment_details.sector:
        table_data.append(
            ["Sector", Paragraph(safe_str(investment_details.sector))]
        )
    if investment_details.sub_sector:
        table_data.append(
            ["Sub Sector", Paragraph(safe_str(investment_details.sub_sector))]
        )

    if y_position - (len(table_data) * 15) < 100:
        pdf.showPage()
        add_header()
        y_position = start_height - 3 * line_height

    table = Table(table_data, colWidths=[200, 300])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )

    table.wrapOn(pdf, left_margin, y_position)
    table.drawOn(pdf, left_margin, y_position - (len(table_data) * 15))
    y_position -= (len(table_data) * 15) + 30

    blue_row_data = [["Land Details"]]
    blue_row_table = Table(blue_row_data, colWidths=[500])
    blue_row_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1669ae")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    blue_row_table.wrapOn(pdf, left_margin, y_position)
    blue_row_table.drawOn(pdf, left_margin, y_position - (1 * 5))
    y_position -= (2 * 8) + 10

    table_data = []

    have_you_identified_land = safe_str(investment_details.do_you_have_land)
    if have_you_identified_land and have_you_identified_land.lower() == "true":
        table_data.append(["Have you identified land?", "Yes"])

        land_type = safe_str(investment_details.type_of_land)
        if land_type:
            table_data.append(["Land Type", Paragraph(land_type)])

            # Common: Total Land
            if investment_details.total_land_area:
                table_data.append(["Total land (sqm)", safe_str(investment_details.total_land_area)])

            # Case for specific land types
            if land_type in ["MSME", "MPIDC", "MPSEDC"]:
                if investment_details.industrial_area:
                    table_data.append([f"{land_type} Industrial Areas", Paragraph(safe_str(investment_details.industrial_area))])
                if investment_details.land_district:
                    table_data.append(["District", safe_str(investment_details.land_district)])
                # if investment_details.land_pincode:
                    # table_data.append(["Pin code", safe_str(investment_details.land_pincode)])

            elif land_type in ["Private land in planned area", "Private land in unplanned area"]:
                if investment_details.land_address:
                    table_data.append(["Address of Land", Paragraph(safe_str(investment_details.land_address))])
                if investment_details.land_district:
                    table_data.append(["District", safe_str(investment_details.land_district)])
                if investment_details.land_pincode:
                    table_data.append(["PIN Code", safe_str(investment_details.land_pincode)])
    else:
        preffered_district = safe_str(intention_data.preffered_district)
        if preffered_district:
            district_pairs = preffered_district.split("||")
            district_names = [pair.split(":")[1] for pair in district_pairs if ":" in pair]
            preffered_district_str = ", ".join(district_names)
            table_data.append(["Have you identified land", "No"])
            table_data.append(["Preferred District", Paragraph(preffered_district_str)])

        if investment_details.total_land_area:
            table_data.append([
                "Total land requirement",
                safe_str(investment_details.total_land_area),
            ])


    if y_position - (len(table_data) * 15) < 100:
        pdf.showPage()
        add_header()
        y_position = start_height - 3 * line_height

    table = Table(table_data, colWidths=[200, 300])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )

    table.wrapOn(pdf, left_margin, y_position)
    table.drawOn(pdf, left_margin, y_position - (len(table_data) * 15))
    y_position -= (len(table_data) * 15) + 30

    blue_row_data = [["Investment Details"]]
    blue_row_table = Table(blue_row_data, colWidths=[500])
    blue_row_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1669ae")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    blue_row_table.wrapOn(pdf, left_margin, y_position)
    blue_row_table.drawOn(pdf, left_margin, y_position - (1 * 5))
    y_position -= (2 * 8) + 50

    db_date_string = safe_str(investment_details.product_proposed_date)
    if db_date_string and db_date_string != "NA":
        formatted_date = datetime.strptime(db_date_string, "%Y-%m-%d").strftime(
            "%d/%m/%Y"
        )
    else:
        formatted_date = "NA"

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    table_data = []

    if investment_details.total_investment:
        table_data.append([
            "Proposed Investment (in Lakhs)",
            safe_str(investment_details.total_investment),
        ])

    if investment_details.plant_machinary_value:
        table_data.append([
            Paragraph("Proposed Investment in Plant & Machinery (in Lakhs)"),
            safe_str(investment_details.plant_machinary_value),
        ])

    if formatted_date:
        table_data.append([
            "Proposed Date for Production",
            formatted_date,
        ])

    if investment_details.total_employee:
        table_data.append([
            "Total Number of Employees",
            safe_str(investment_details.total_employee),
        ])
    if investment_details.power_limit:
        table_data.append([
            "Requirement of Power (in KW)",
            safe_str(investment_details.power_limit),
        ])
    if investment_details.water_limit:
        table_data.append([
            "Requirement of Water (in KL)",
            safe_str(investment_details.water_limit),
        ])

    if investment_details.total_local_employee:
        table_data.append([
            "Total employees having MP domicle",
            safe_str(investment_details.total_local_employee),
        ])

    export = investment_details.export_oriented_unit  # Boolean
    question = Paragraph("Do you operate as an Export-Oriented Unit?", normal_style)
    value = Paragraph("Yes" if export else "No", normal_style)
    table_data.append([question, value])

    # Question 2: Export % range (conditionally)
    if export and investment_details.export_percentage is not None:
        percentage = float(investment_details.export_percentage)
        if percentage <= 50:
            export_range = "0%-50%"
        elif percentage <= 75:
            export_range = "50%-75%"
        else:
            export_range = "75%-100%"

        table_data.append([
            Paragraph("Export %", normal_style),
            Paragraph(export_range, normal_style)
        ])

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),       
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),         
    ]))

    if y_position - (len(table_data) * 15) < 150:
        pdf.showPage()
        add_header()
        y_position = start_height - 3 * line_height

    table = Table(table_data, colWidths=[200, 300])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )

    table.wrapOn(pdf, left_margin, y_position)
    table.drawOn(pdf, left_margin, y_position - (len(table_data) * 15))
    y_position -= (len(table_data) * 15) + 30

    if y_position - (len(table_data) * 15) < 150:
        pdf.showPage()
        y_position = start_height - 3 * line_height

    blue_row_data = [["Company Details"]]
    blue_row_table = Table(blue_row_data, colWidths=[500])
    blue_row_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1669ae")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    blue_row_table.wrapOn(pdf, left_margin, y_position)
    blue_row_table.drawOn(pdf, left_margin, y_position - (1 * 5))
    y_position -= (2 * 8) + 13

    table_data = []

    if caf.name:
        table_data.append(["Name of Organization", safe_str(caf.name)])

    if caf.scale_of_industry:
        table_data.append(["Industry Scale", safe_str(caf.scale_of_industry)])

    if caf.firm_pan_number:
        table_data.append(["Firm PAN No.", safe_str(caf.firm_pan_number)])

    if caf.firm_gstin_number:
        table_data.append(["Firm GSTIN No.", safe_str(caf.firm_gstin_number)])

    if caf.firm_registration_number:
        table_data.append(["Corporate Identification Number", safe_str(caf.firm_registration_number)])

    if y_position - (len(table_data) * 15) < 100:
        pdf.showPage()
        y_position = start_height - 3 * line_height

    table = Table(table_data, colWidths=[200, 300])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )

    table.wrapOn(pdf, left_margin, y_position)
    table.drawOn(pdf, left_margin, y_position - (len(table_data) * 15))
    y_position -= (len(table_data) * 15) + 50

    blue_row_data = [["Contact Details"]]
    blue_row_table = Table(blue_row_data, colWidths=[500])
    blue_row_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1669ae")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    blue_row_table.wrapOn(pdf, left_margin, y_position)
    blue_row_table.drawOn(pdf, left_margin, y_position - (1 * 5))
    y_position -= (2 * 8) + 12

    table_data = []

    if common_applications.name:
        table_data.append(["Authorized Person Name", safe_str(common_applications.name)])

    if common_applications.designation:
        if common_applications.designation.lower() == "other" and common_applications.other_designation:
            table_data.append([
                "Designation",
                safe_str(common_applications.designation),
            ])
            table_data.append([
                "Other Designation",
                safe_str(common_applications.other_designation),
            ])
        else:
            table_data.append([
                "Designation",
                safe_str(common_applications.designation)
            ])

    if common_applications.mobile_number:
        table_data.append(["Mobile Number", safe_str(common_applications.mobile_number)])

    if common_applications.email_id:
        table_data.append(["Email ID", safe_str(common_applications.email_id)])

    if y_position - (len(table_data) * 15) < 100:
        pdf.showPage()
        y_position = start_height - 3 * line_height

    table = Table(table_data, colWidths=[200, 300])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )

    table.wrapOn(pdf, left_margin, y_position)
    table.drawOn(pdf, left_margin, y_position - (len(table_data) * 15))
    y_position -= (len(table_data) * 15) + 50

    if "reg_address" in addresses:
        blue_row_data = [["Registered Address Details"]]
        blue_row_table = Table(blue_row_data, colWidths=[500])
        blue_row_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1669ae")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        blue_row_table.wrapOn(pdf, left_margin, y_position)
        blue_row_table.drawOn(pdf, left_margin, y_position - (1 * 5))
        y_position -= (2 * 8) + 12

        table_data = []

        reg_address = addresses.get("reg_address", {})

        if safe_str(reg_address.address_line):
            table_data.append(["Address Line", safe_str(reg_address.address_line)])

        if safe_str(reg_address.state):
            table_data.append(["State", safe_str(title_case(reg_address.state))])

        if safe_str(reg_address.district):
            table_data.append(["District", safe_str(reg_address.district)])

        if safe_str(reg_address.pin_code):
            table_data.append(["PIN Code", safe_str(reg_address.pin_code)])


        if y_position - (len(table_data) * 15) < 100:
            pdf.showPage()
            y_position = start_height - 3 * line_height

        table = Table(table_data, colWidths=[200, 300])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )

        table.wrapOn(pdf, left_margin, y_position)
        table.drawOn(pdf, left_margin, y_position - (len(table_data) * 15))
        y_position -= (len(table_data) * 15) + 50

    if "comm_address" in addresses:
        blue_row_data = [["Communication Address Details"]]
        blue_row_table = Table(blue_row_data, colWidths=[500])
        blue_row_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1669ae")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        blue_row_table.wrapOn(pdf, left_margin, y_position)
        blue_row_table.drawOn(pdf, left_margin, y_position - (1 * 5))
        y_position -= (2 * 8) + 12

        table_data = []

        comm_address = addresses.get("comm_address", {})

        if safe_str(comm_address.address_line):
            table_data.append(["Address Line", safe_str(comm_address.address_line)])

        if safe_str(comm_address.state):
            table_data.append(["State", safe_str(title_case(comm_address.state))])

        if safe_str(comm_address.district):
            table_data.append(["District", safe_str(comm_address.district)])

        if safe_str(comm_address.pin_code):
            table_data.append(["PIN Code", safe_str(comm_address.pin_code)])
       

        if y_position - (len(table_data) * 15) < 100:
            pdf.showPage()
            y_position = start_height - 3 * line_height

        table = Table(table_data, colWidths=[200, 300])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )

        table.wrapOn(pdf, left_margin, y_position)
        table.drawOn(pdf, left_margin, y_position - (len(table_data) * 15))
        y_position -= (len(table_data) * 15) + 50

    if y_position < 100:
        pdf.showPage()
        y_position = start_height - 3 * line_height

    draw_wrapped_text(
        "I/We further solemnly affirm that the mentioned declaration is correct to the best of my/our knowledge and belief and no fact has been suppressed in this connection."
    )

    check_space(3 * line_height)
    text = "Thanking you,"
    text_width = pdf.stringWidth(text, "Helvetica", 11)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(left_margin, y_position, text)
    y_position -= 2 * line_height

    left_x, right_x = 50, 400
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(left_x, y_position, "Place: Bhopal")
    pdf.drawString(right_x, y_position, f"Investor Name: {customer_data.name}")
    pdf.drawString(
        left_x, y_position - line_height, f"Date: {datetime.now().strftime('%d/%m/%Y')}"
    )
    pdf.drawString(
        right_x, y_position - line_height, f"Mobile No: {customer_data.mobile_no}"
    )
    pdf.drawString(
        right_x, y_position - 2 * line_height, f"Email ID: {customer_data.email}"
    )

    pdf.save()
    buffer.seek(0)

    # Ensure the directory exists
    pdf_directory = os.path.join(settings.MEDIA_ROOT, "caf_investment_pdfs")
    os.makedirs(pdf_directory, exist_ok=True)

    file_name = f"CAF_Investment_{caf.id}_{caf_reference_id}.pdf"
    file_path = os.path.join(pdf_directory, file_name)

    with open(file_path, "wb") as f:
        f.write(buffer.getvalue())

    with open(file_path, "rb") as file_to_upload:
        doc_file = SimpleUploadedFile(
            name=file_name,
            content=file_to_upload.read(),
            content_type="application/pdf",
        )

    documents = [
        {
            "file": doc_file,
            "file_name": doc_file.name,
            "file_type": doc_file.content_type,
        }
    ]

    document_folder = (
        customer_data.document_folder
        if customer_data.document_folder
        else customer_data.user_id
    )
    url = settings.MINIO_API_HOST + "/minio/uploads"

    upload_response = upload_files_to_minio(documents, url, document_folder)

    if not upload_response["success"]:
        return Response(
            {
                "status": False,
                "message": "File upload failed",
                "error": upload_response["error"],
                "server_response": upload_response["response"],
            },
            status=500,
        )

    file_url = f"{settings.MEDIA_URL}caf_investment_pdfs/{file_name}"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        return Response({"status": False, "message": global_err_message}, status=500)

    # Save to database
    caf_pdf, created = CAFCreationPDF.objects.update_or_create(
        caf=caf,
        defaults={
            "pdf_url": upload_response["data"][0]["path"],
            "caf_doc": upload_response["data"][0]["path"],
            "caf_reference_id": caf_reference_id,
        },
    )

    return upload_response["data"][0]["path"]


def safe_str(value):
    """Convert values to safe UTF-8 encoded strings."""
    try:
        return str(value).encode("utf-8", "ignore").decode("utf-8")
    except UnicodeDecodeError:
        return "Invalid Data"


def generate_intention_form_pdf(intention_data, customer_data):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    left_margin, right_margin = 50, 50
    start_height, line_height = 800, 18
    page_width, page_height = A4
    y_position = start_height

    def check_space(height_required):
        nonlocal y_position
        if y_position - height_required < 50:
            pdf.showPage()
            add_header()
            y_position = start_height
            return True
        return False

    def add_header():
        """Adds header with MPIDC logo and title on new page."""
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawRightString(
            page_width - right_margin,
            start_height,
            "MP Industrial Development Corporation Ltd.",
        )
        pdf.setFont("Helvetica", 12)
        pdf.drawRightString(
            page_width - right_margin,
            start_height - line_height,
            "21, Arera Hills, Bhopal, 462011",
        )
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(
            left_margin, start_height - 3 * line_height, "INTENTION TO INVEST"
        )

    logo_url = os.path.join(settings.MEDIA_ROOT, 'mpidc-pdf-logo.png')
    logo = ImageReader(logo_url)
    pdf.drawImage(logo, left_margin, y_position - 15, width=80, height=30, mask="auto")

    add_header()
    y_position -= 5 * line_height

    pdf.setFont("Helvetica-Bold", 12)
    application_text = (
        f"Application No.: {safe_str(intention_data.get('intention_id', 'NA'))}"
    )
    date_text = f"Date: {datetime.now().strftime('%d %b %Y')}"
    date_text_width = pdf.stringWidth(date_text, "Helvetica-Bold", 12)
    right_position = page_width - right_margin - date_text_width

    pdf.drawString(left_margin, y_position, application_text)
    pdf.drawString(right_position, y_position, date_text)
    y_position -= 3 * line_height

    check_space(5 * line_height)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(left_margin, y_position, "To,")
    pdf.drawString(left_margin, y_position - line_height, "The Executive Director,")
    pdf.drawString(
        left_margin,
        y_position - 2 * line_height,
        f"Subject: Regarding Intention to Invest having Application Number {safe_str(intention_data.get('intention_id', 'NA'))}",
    )
    y_position -= 5 * line_height
    pdf.drawString(left_margin, y_position, "Dear Sir/Madam,")
    y_position -= line_height

    def draw_wrapped_text(text, max_width=500):
        """Draw wrapped text dynamically, adjusting for new pages."""
        nonlocal y_position
        words = text.split()
        line = ""
        for word in words:
            if pdf.stringWidth(line + word, "Helvetica", 12) < max_width:
                line += word + " "
            else:
                check_space(line_height)
                pdf.drawString(left_margin, y_position, line.strip())
                y_position -= line_height
                line = word + " "
        check_space(line_height)
        pdf.drawString(left_margin, y_position, line.strip())
        y_position -= line_height

    draw_wrapped_text(
        f"We would like to request to please check all the mentioned details of Intention to Invest (ID: {safe_str(intention_data.get('intention_id', 'NA'))}), for Plot Number, Industrial Area Acharpura Industrial Area, District Bhopal."
    )
    y_position -= 3 * line_height

    table_data = [
        ["Proposed Product Details"],
        ["Activity Name", safe_str(intention_data.get("activity", "NA"))],
        ["Sector", safe_str(intention_data.get("sector", "NA"))],
        ["Product Name", safe_str(intention_data.get("product_name", "NA"))],
        [
            "Product Proposed Date",
            safe_str(intention_data.get("product_proposed_date", "NA")),
        ],
        [
            "Project Description",
            safe_str(intention_data.get("project_description", "NA")),
        ],
        ["Total Investment", safe_str(intention_data.get("total_investment", "NA"))],
        ["Power Required (KW)", safe_str(intention_data.get("power_required", "NA"))],
        ["Employment", safe_str(intention_data.get("employment", "NA"))],
        ["Company Name", safe_str(intention_data.get("company_name", "NA"))],
        ["Investment Type", safe_str(intention_data.get("investment_type", "NA"))],
        ["Sub Sector", safe_str(intention_data.get("sub_sector", "NA"))],
        ["Investment In PM", safe_str(intention_data.get("investment_in_pm", "NA"))],
        [
            "Total Land Required",
            safe_str(intention_data.get("total_land_required", "NA")),
        ],
    ]
    if intention_data.get("land_identified") == "true":
        land_type = safe_str(intention_data.get("land_type", "NA"))
        if land_type in ["MSME", "MPIDC", "MPSEDC"]:
            table_data += [
                ["Land Type", safe_str(intention_data.get("land_type", "NA"))],
                [
                    "Land Industrial Area",
                    safe_str(intention_data.get("land_industrial_area", "NA")),
                ],
            ]
        else:
            table_data += [
                ["Land Type", safe_str(intention_data.get("land_type", "NA"))],
                ["District", safe_str(intention_data.get("district", "NA"))],
                ["Address", safe_str(intention_data.get("address", "NA"))],
                ["Pincode", safe_str(intention_data.get("pincode", "NA"))],
            ]
    else:
        preffered_district = safe_str(intention_data.get("preffered_district", []))
        if preffered_district:
            district_pairs = preffered_district.split("||")
            district_names = [pair.split(":")[1] for pair in district_pairs]
            preffered_district = ", ".join(district_names)
        table_data.append(["Prefferred Districts", preffered_district])

    if y_position - (len(table_data) * 15) < 100:
        pdf.showPage()
        add_header()
        y_position = start_height - 3 * line_height

    table = Table(table_data, colWidths=[200, 300])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1b92ce")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    table.wrapOn(pdf, left_margin, y_position)
    table.drawOn(pdf, left_margin, y_position - (len(table_data) * 15))
    y_position -= (len(table_data) * 15) + 20

    if y_position < 150:
        pdf.showPage()
        add_header()
        y_position = start_height - 3 * line_height

    draw_wrapped_text(
        "I/We further solemnly affirm that the aforementioned declaration is correct to the best of my/our knowledge and belief and no fact has been suppressed in this connection."
    )

    check_space(3 * line_height)
    text = "Thanking you,"
    text_width = pdf.stringWidth(text, "Helvetica", 12)
    pdf.setFont("Helvetica", 12)
    pdf.drawString((page_width - text_width) / 2, y_position, text)
    y_position -= 5 * line_height

    left_x, right_x = 50, 400
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left_x, y_position, "Place: Bhopal")
    pdf.drawString(right_x, y_position, f"Investor Name: {customer_data.name}")
    pdf.drawString(
        left_x, y_position - line_height, f"Date: {datetime.now().strftime('%d %b %Y')}"
    )
    pdf.drawString(
        right_x, y_position - line_height, f"Mobile No: {customer_data.mobile_no}"
    )

    pdf.drawString(
        right_x, y_position - 2 * line_height, f"Email ID: {customer_data.email}"
    )

    pdf.save()
    buffer.seek(0)

    file_name = f"intention_{intention_data['intention_id']}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, "intention_pdfs", file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(buffer.getvalue())

    with open(file_path, "rb") as file_to_upload:
        doc_file = SimpleUploadedFile(
            name=file_name,
            content=file_to_upload.read(),
            content_type="application/pdf",
        )
    documents = [
        {
            "file": doc_file,
            "file_name": doc_file.name,
            "file_type": doc_file.content_type,
        }
    ]
    document_folder = (
        customer_data.document_folder
        if customer_data.document_folder
        else customer_data.user_id
    )
    url = settings.MINIO_API_HOST + "/minio/uploads"

    upload_response = upload_files_to_minio(documents, url, document_folder)

    if not upload_response["success"]:
        return Response(
            {
                "status": False,
                "message": "File upload failed",
                "error": upload_response["error"],
                "server_response": upload_response["response"],
            },
            status=500,
        )

    # file_url = f"{settings.MEDIA_URL}intention_pdfs/{file_name}"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        return Response({"status": False, "message": global_err_message}, status=500)

    return upload_response["data"][0]["path"]


# USER PROFILE PDF GENERATE
def generate_user_profile_pdf(user):
    """Generates a PDF with user details and returns the file URL."""

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    left_margin, right_margin = 50, 50
    start_height, line_height = 800, 18
    page_width = A4[0]
    y_position = start_height

    # ✅ Fetch organization details **before using it**
    organization = UserOrgazination.objects.filter(user_profile=user).first()
    firm_registration_number = (
        organization.firm_registration_number if organization else "N/A"
    )

    # ✅ Load & Add MPIDC Logo (Left Side)
    logo_url = os.path.join(settings.MEDIA_ROOT, 'mpidc-pdf-logo.png')
    logo = ImageReader(logo_url)
    pdf.drawImage(logo, left_margin, y_position - 15, width=80, height=30, mask="auto")

    # ✅ Add Registration No on the Right Side
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(
        page_width - right_margin,
        y_position,
        f"Registration No: {firm_registration_number}",
    )

    # ✅ Fetch user-related data (AFTER fetching organization)
    user_profile = CustomUserProfile.objects.filter(user=user).first()
    user_contacts = UserProfile.objects.filter(organization__user_profile=user)
    org_address = OrganizationAddress.objects.filter(organization=organization)

    # ✅ Move Down Before Adding Firm Details
    y_position -= 3 * line_height

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left_margin, y_position, "Firm/Company Details")
    pdf.setFont("Helvetica", 12)

    # ✅ Adjust Y-Position Dynamically After Each Field
    y_position -= line_height
    pdf.drawString(
        left_margin,
        y_position,
        f"Type of Organization: {organization.organization_type}",
    )

    y_position -= line_height
    pdf.drawString(left_margin, y_position, f"Firm / Company Name: {organization.name}")

    y_position -= line_height
    pdf.drawString(
        left_margin, y_position, f"Telephone No.: {organization.helpdesk_number}"
    )

    y_position -= line_height
    pdf.drawString(
        left_margin,
        y_position,
        f"Firm / Company PAN No.: {organization.firm_pan_number}",
    )

    y_position -= line_height
    pdf.drawString(
        left_margin,
        y_position,
        f"Firm / Company GSTIN No.: {organization.firm_gstin_number}",
    )

    y_position -= line_height
    pdf.drawString(
        left_margin,
        y_position,
        f"Firm Registration number: {organization.firm_registration_number}",
    )

    y_position -= line_height
    pdf.drawString(
        left_margin,
        y_position,
        f"Firm Registration Date: {organization.registration_date.strftime('%d %b %Y') if organization.registration_date else 'N/A'}",
    )

    y_position -= line_height
    pdf.drawString(
        left_margin,
        y_position,
        f"Weather your organization is Categorised as MSME (Medium Small and Micro Enterprise): {'YES' if organization.registered_under_msme else 'NO'}",
    )

    # ✅ Ensure Proper Spacing for the Next Section
    y_position -= 3 * line_height

    # ✅ Fetch Registered Office Address
    registered_office = OrganizationAddress.objects.filter(
        organization=organization, address_type="Registered"
    ).first()

    # ✅ Format Address Fields (Handle Missing Data)
    address_line = registered_office.address_line if registered_office else "N/A"
    district = (
        registered_office.district.name
        if registered_office and registered_office.district
        else "N/A"
    )
    state = (
        registered_office.state.name
        if registered_office and registered_office.state
        else "N/A"
    )
    pin_code = registered_office.pin_code if registered_office else "N/A"

    # ✅ Registered Office Address Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left_margin, y_position, "Address of Registered Office")
    pdf.setFont("Helvetica", 12)

    pdf.drawString(
        left_margin, y_position - line_height, f"Address Line: {address_line}"
    )
    pdf.drawString(left_margin, y_position - 2 * line_height, f"District: {district}")
    pdf.drawString(left_margin, y_position - 3 * line_height, f"State: {state}")
    pdf.drawString(left_margin, y_position - 4 * line_height, f"Pin Code: {pin_code}")

    # ✅ Move Down for Next Section
    y_position -= 5 * line_height

    # ✅ User Details
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left_margin, y_position, "User Details")
    pdf.setFont("Helvetica", 12)

    pdf.drawString(
        left_margin,
        y_position - line_height,
        f"Name: {user_profile.name if user_profile else 'N/A'}",
    )
    pdf.drawString(
        left_margin,
        y_position - 2 * line_height,
        f"Mobile No: {user_profile.mobile_no if user_profile else 'N/A'}",
    )
    pdf.drawString(
        left_margin,
        y_position - 3 * line_height,
        f"Email: {user.email if user else 'N/A'}",
    )

    y_position -= 6 * line_height

    y_position -= 3 * line_height

    # ✅ Address Details
    if org_address.exists():
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(left_margin, y_position, "Organization Address")
        pdf.setFont("Helvetica", 12)

        for address in org_address:
            pdf.drawString(
                left_margin, y_position - line_height, f"Type: {address.address_type}"
            )
            pdf.drawString(
                left_margin,
                y_position - 2 * line_height,
                f"Address: {address.address_line}",
            )
            pdf.drawString(
                left_margin,
                y_position - 3 * line_height,
                f"District: {address.district.name}",
            )
            pdf.drawString(
                left_margin,
                y_position - 4 * line_height,
                f"State: {address.state.name}",
            )
            pdf.drawString(
                left_margin,
                y_position - 5 * line_height,
                f"Pin Code: {address.pin_code}",
            )
            y_position -= 7 * line_height  # Adjust spacing for multiple addresses

    # ✅ Contact Details
    if user_contacts.exists():
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(left_margin, y_position, "Contact Details")
        pdf.setFont("Helvetica", 12)

        for contact in user_contacts:
            pdf.drawString(
                left_margin, y_position - line_height, f"Name: {contact.name}"
            )
            pdf.drawString(
                left_margin,
                y_position - 2 * line_height,
                f"Designation: {contact.designation}",
            )
            pdf.drawString(
                left_margin,
                y_position - 3 * line_height,
                f"Mobile: {contact.mobile_number}",
            )
            pdf.drawString(
                left_margin, y_position - 4 * line_height, f"Email: {contact.email_id}"
            )
            y_position -= 6 * line_height  # Adjust for each contact

    # ✅ Save PDF
    pdf.save()
    buffer.seek(0)

    # ✅ Save PDF file
    pdf_directory = os.path.join(settings.MEDIA_ROOT, "user_profile_pdfs")
    os.makedirs(pdf_directory, exist_ok=True)

    file_name = f"User_Profile_{user.id}.pdf"
    file_path = os.path.join(pdf_directory, file_name)

    with open(file_path, "wb") as f:
        f.write(buffer.getvalue())

    with open(file_path, "rb") as file_to_upload:
        doc_file = SimpleUploadedFile(
            name=file_name,
            content=file_to_upload.read(),
            content_type="application/pdf",
        )

    documents = [
        {
            "file": doc_file,
            "file_name": doc_file.name,
            "file_type": doc_file.content_type,
        }
    ]

    document_folder = (
        user_profile.document_folder
        if user_profile.document_folder
        else user_profile.user_id
    )
    url = settings.MINIO_API_HOST + "/minio/uploads"

    upload_response = upload_files_to_minio(documents, url, document_folder)

    if not upload_response["success"]:
        return Response(
            {
                "status": False,
                "message": "File upload failed",
                "error": upload_response["error"],
                "server_response": upload_response["response"],
            },
            status=500,
        )

    file_url = f"{settings.MEDIA_URL}caf_investment_pdfs/{file_name}"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        return Response({"status": False, "message": global_err_message}, status=500)

    file_url = f"{settings.MEDIA_URL}user_profile_pdfs/{file_name}"

    UserProfilePDF.objects.update_or_create(
        user=user,
        defaults={
            "user_pdf_file": upload_response["data"][0]["path"],
            "doc_url": upload_response["data"][0]["path"],
        },
    )

    return upload_response["data"][0]["path"]


def title_case(text):
    """Converts the first letter of each word to uppercase and the rest to lowercase."""
    return " ".join(word.capitalize() for word in text.split())

def get_industry_scale(intention_data):
    if float(intention_data.investment_in_pm) <= 2.5:
        return "Micro"
    elif float(intention_data.investment_in_pm) > 2.5 and float(intention_data.investment_in_pm) <= 25:
        return "Small"
    elif float(intention_data.investment_in_pm) > 25 and float(intention_data.investment_in_pm) <= 125:
        return "Medium"
    elif float(intention_data.investment_in_pm) > 125:
        return "Large"


def create_service_url(config_data, service_data):
    url = config_data.redirect_url
    service_id = service_data['id']
    url = url + "?service_id="+str(service_id)
    return url
