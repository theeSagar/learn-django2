import io, os, uuid, math, logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.response import Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.platypus import Table, TableStyle, Paragraph
from .models import *
from userprofile.models import *
from document_center.utils import upload_files_to_minio
logger = logging.getLogger(__name__)
from authentication.models import CustomUserProfile
from userprofile.models import OrganizationUserModel
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE
from reportlab.lib.styles import getSampleStyleSheet
import base64
from PyPDF2 import PdfReader
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from reportlab.platypus import Image, Spacer
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib.fonts import addMapping
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# pdfmetrics.registerFont(
#     TTFont("NotoSansDevanagari-Regular", os.path.join(BASE_DIR, "incentive", "fonts", "NotoSansDevanagari-VariableFont_wdth,wght.ttf"))
# )
# pdfmetrics.registerFont(
#     TTFont("NotoSansDevanagari-Bold", os.path.join(BASE_DIR, "incentive", "fonts", "NotoSansDevanagari-Bold.ttf"))
# )
font_regular_path = os.path.join(settings.MEDIA_ROOT, "NotoSansDevanagari-VariableFont_wdth,wght.ttf")
font_bold_path = os.path.join(settings.MEDIA_ROOT, "NotoSansDevanagari-Bold.ttf")
pdfmetrics.registerFont(TTFont("NotoSansDevanagari-Regular", font_regular_path))
pdfmetrics.registerFont(TTFont("NotoSansDevanagari-Bold", font_bold_path))
addMapping("NotoSansDevanagari-Regular", 0, 0, "NotoSansDevanagari-Regular")  
addMapping("NotoSansDevanagari-Regular", 1, 0, "NotoSansDevanagari-Bold")     



def calculateBipa(investment):
    if investment > 2000:
        return 200
    elif investment <= 50:
        return 0.4 * investment
    else:
        term1 = 15 + 0.08 * (investment - 50)
        term2 = (investment / 12) * (1 / (1 + math.exp(-5.9 * (1 - investment / 2490)))) * (1 - investment / 2490)
        term3 = 9.3 * (1 - investment / 2500)
        result = term1 + term2 + term3
        return min(result, 0.4 * investment, 200)
    

def sectorMultiplier(request, sector_name):
    sectormapping = Sector.objects.filter(id=sector_name,show_in_incentive_calc=True).first()
    if sectormapping:
        if sectormapping.incentive_name == 'Pharmaceuticals':
            is_bulk_order_company = get_bool_param(request, "is_bulk_order_company", False)
            if is_bulk_order_company:
                return 1.3
        elif sectormapping.incentive_name == 'Agri, Dairy, and Food Processing':
            is_carbonated_industry = get_bool_param(request, "is_carbonated_industry", False)
            if is_carbonated_industry:
                return 1.0
        return float(sectormapping.sector_multiple)
    return 1.0

def calculate_sector_amount(sector_multiplier, bipa):
    if sector_multiplier == 0:
        return 0
    else:
        return sector_multiplier * bipa - bipa
    
def calculate_gsm_multiplier(forty_percent, cyp, yuc):
    min_value = min(forty_percent, cyp / yuc)
    return min_value / forty_percent

def calculate_employee_multiple(total_employer):
    if total_employer < 100:
        return 1
    elif total_employer > 2500:
        return 1.5
    else:
        return 1 + ((total_employer - 100) / (2500 - 100)) * (1.5 - 1)
    
def calculate_export_percent(export_per):
    if export_per < 25:
        return 1
    elif export_per > 75:
        return 1.3
    else:
        return 1 + ((export_per - 25) / (75 - 25)) * (1.3 - 1)

def calculate_fdi_multiple(fdi_per):
    if fdi_per < 26:
        return 1
    elif fdi_per <= 51:
        return 1.1 + (fdi_per - 26) * (0.1 / (51 - 26))
    else:
        return 1.2
    
def calculate_subsidy_amount(*args):
    total = 0
    for value in args:
        if isinstance(value, (int, float)):
            total += value
    return total

def get_int_param(request, param_name, default_value):
    param = request.query_params.get(param_name, "").strip()
    try:
        value = int(param) if param else default_value
        if value > 0:
            return value
        return default_value
    except ValueError:
        return default_value

def get_float_param(request, param_name, default_value):
    param = request.query_params.get(param_name, "").strip()
    try:
        value = float(param) if param else default_value
        if value > 0:
            return value
        return default_value
    except ValueError:
        return default_value

def get_bool_param(request, param_name, default_value):
    param = request.query_params.get(param_name, "").strip().lower()
    try:
        return param == "true" if param in ["true", "false"] else default_value
    except ValueError:
        return default_value


def get_sector_specific_details(request, sector_name):
    sector_incentive = {}
    sector_mapping = Sector.objects.filter(id=sector_name,show_in_incentive_calc=True).first()

    if sector_mapping and sector_mapping.incentive_method:
        func = globals().get(sector_mapping.incentive_method)
        if callable(func):
            sector_incentive = func(request)
        else:
            sector_incentive = get_general_incentive(request)
    else:
        sector_incentive = get_general_incentive(request)
    return sector_incentive

def common_incentive(request):
    sector_incentive = {}

    is_iwms = get_bool_param(request, "is_iwms", False)
    if is_iwms:
        sector_incentive['wms'] = round(get_float_param(request, "wms", 0) * 0.5,2)
        is_zld = get_bool_param(request, "is_zld", False)
        if is_zld:
            if sector_incentive['wms'] > 10:
                sector_incentive['wms'] = 10
        else:
            if sector_incentive['wms'] > 5:
                sector_incentive['wms'] = 5

    #For Intellectual Property Rights 
    sector_incentive['ipr'] = round(get_float_param(request, "ipr", 0),2)
    if sector_incentive['ipr'] > 0.1:
        sector_incentive['ipr'] = 0.1

    landtype = get_int_param(request, "landtype", 0)
    if landtype in [1, 2]:
        sector_incentive['ida'] = round(get_float_param(request, "ida", 0) * 0.5,2)
        if sector_incentive['ida'] > 5:
            sector_incentive['ida'] = 5
    
    sector_incentive['export_freight'] = round(get_float_param(request, "export_freight", 0) * 0.5,2)
    if sector_incentive['export_freight'] >= 2:
        sector_incentive['export_freight'] = 2
    
    return sector_incentive


def get_agri_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['electricity_units'] = round(get_float_param(request, "electricity_units", 0)/10000000, 2)
    sector_incentive['mandii_fee'] = round(get_float_param(request, "mandii_fee", 0), 2)
    incentive_plant_machinery = round(get_float_param(request, "incentive_plant_machinery", 0) * 0.5, 2)
    if sector_incentive['mandii_fee'] > incentive_plant_machinery:
        sector_incentive['mandii_fee'] = incentive_plant_machinery
    sector_incentive['qci'] = round(get_float_param(request, "qci", 0) * 0.5, 2)
    if sector_incentive['qci'] > 0.05:
        sector_incentive['qci'] = 0.05
    sector_incentive['oca'] = round(get_float_param(request, "oca", 0), 2)
    if sector_incentive['oca'] > 0.05:
        sector_incentive['oca'] = 0.05
    return sector_incentive

def get_textile_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['interest_subsidy'] = round(get_float_param(request, "interest_subsidy", 0) * 0.05, 2)
    if sector_incentive['interest_subsidy'] > 50:
        sector_incentive['interest_subsidy'] = 50
    sector_incentive['oca'] = round(get_float_param(request, "oca", 0), 2)
    if sector_incentive['oca'] > 0.05:
        sector_incentive['oca'] = 0.05    
    sector_incentive['apparel_training'] = round(get_float_param(request, "apparel_training", 0) * 0.25, 2)
    if sector_incentive['apparel_training'] > 0.5:
        sector_incentive['apparel_training'] = 0.5
    return sector_incentive

def get_garment_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['electricity_units'] = round(get_float_param(request, "electricity_units", 0)/10000000, 2)
    sector_incentive['interest_subsidy'] = round(get_float_param(request, "interest_subsidy", 0) * 0.05, 2)
    if sector_incentive['interest_subsidy'] > 50:
        sector_incentive['interest_subsidy'] = 50
    new_employee_tsd = get_int_param(request, "total_employer", 0)
    if new_employee_tsd > 4000:
        sector_incentive['new_employee_tsd'] = round(4000 * 0.0013,2)
    else:
        sector_incentive['new_employee_tsd'] = round(new_employee_tsd * 0.0013, 2)
    sector_incentive['oca'] = round(get_float_param(request, "oca", 0), 2)
    if sector_incentive['oca'] > 0.05:
        sector_incentive['oca'] = 0.05
    
    sector_incentive['apparel_training'] = round(get_float_param(request, "apparel_training", 0) * 0.25, 2)
    if sector_incentive['apparel_training'] > 0.5:
        sector_incentive['apparel_training'] = 0.5

    return sector_incentive


def get_aerodefence_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['qci'] = round(get_float_param(request, "qci", 0) * 0.5, 2)
    if sector_incentive['qci'] > 0.1:
        sector_incentive['qci'] = 0.1
    
    return sector_incentive

def get_pharma_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['interest_subsidy'] = round(get_float_param(request, "interest_subsidy", 0) * 0.05, 2)
    if sector_incentive['interest_subsidy'] > 25:
        sector_incentive['interest_subsidy'] = 25
    sector_incentive['oca'] = round(get_float_param(request, "oca", 0), 2)
    if sector_incentive['oca'] > 0.05:
        sector_incentive['oca'] = 0.05
    sector_incentive['qci'] = round(get_float_param(request, "qci", 0) * 0.5, 2)
    if sector_incentive['qci'] > 1:
        sector_incentive['qci'] = 1
    sector_incentive['testing_facility'] = round(get_float_param(request, "testing_facility", 0) * 0.5, 2)
    if sector_incentive['testing_facility'] > 1:
        sector_incentive['testing_facility'] = 1
    sector_incentive['assistace_on_r_and_d'] = round(get_float_param(request, "incentive_plant_machinery", 0) * 0.5, 2)
    
    return sector_incentive

def get_biotech_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['oca'] = round(get_float_param(request, "oca", 0), 2)
    if sector_incentive['oca'] > 0.05:
        sector_incentive['oca'] = 0.05
    sector_incentive['testing_facility'] = round(get_float_param(request, "testing_facility", 0) * 0.5, 2)
    if sector_incentive['testing_facility'] > 1:
        sector_incentive['testing_facility'] = 1
    sector_incentive['assistace_on_r_and_d'] = round(get_float_param(request, "incentive_plant_machinery", 0) * 0.5, 2)
    return sector_incentive

def get_medical_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['testing_facility'] = round(get_float_param(request, "testing_facility", 0) * 0.5, 2)
    if sector_incentive['testing_facility'] > 1:
        sector_incentive['testing_facility'] = 1
    sector_incentive['assistace_on_r_and_d'] = round(get_float_param(request, "incentive_plant_machinery", 0) * 0.5, 2)
    return sector_incentive

def get_ev_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['testing_facility'] = round(get_float_param(request, "testing_facility", 0) * 0.5, 2)
    if sector_incentive['testing_facility'] > 1:
        sector_incentive['testing_facility'] = 1
    sector_incentive['qci'] = round(get_float_param(request, "qci", 0) * 0.5, 2)
    if sector_incentive['qci'] > 0.1:
        sector_incentive['qci'] = 0.1
    return sector_incentive

def get_renewable_incentive(request):
    sector_incentive = common_incentive(request)
    sector_incentive['qci'] = round(get_float_param(request, "qci", 0) * 0.5, 2)
    if sector_incentive['qci'] > 0.01:
        sector_incentive['qci'] = 0.01
    return sector_incentive

def get_hv_manufacturing_incentive(request):
    sector_incentive = common_incentive(request)
    new_employee_tsd = get_int_param(request, "total_employer", 0)
    if new_employee_tsd > 4000:
        sector_incentive['new_employee_tsd'] = round(4000 * 0.0013, 2)
    else:
        sector_incentive['new_employee_tsd'] = round(new_employee_tsd * 0.0013, 2)
    sector_incentive['qci'] = round(get_float_param(request, "qci", 0) * 0.5, 2)
    if sector_incentive['qci'] > 0.01:
        sector_incentive['qci'] = 0.01
    sector_incentive['oca'] = round(get_float_param(request, "oca", 0), 2)
    if sector_incentive['oca'] > 0.05:
        sector_incentive['oca'] = 0.05
    return sector_incentive

def get_general_incentive(request):
    sector_incentive = common_incentive(request)
    return sector_incentive

class ActivityHistoryMixin:
    def create_activity_history(
        self,
        caf_instance,
        user_name=None,
        user_role=None,
        ip_address=None,
        activity_status=None,
        caf_status=None,
        status_remark=None,
        activity_result=None,
    ):
        try:
            IncentiveActivityHistory.objects.create(
                caf=caf_instance,
                user_name=user_name,
                user_role=user_role,
                ip_address=ip_address,
                activity_status=activity_status,
                caf_status=caf_status,
                status_remark=status_remark,
                activity_result=activity_result,
            )
            return None  
        except Exception as e:
            logger.error(global_err_message, exc_info=True)
            return Response(
                {
                    "status": False,
                    "message": "Error while creating activity history",
                    "error": global_err_message,
                    "data": {},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



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


def safe_str(value):
    """Convert values to safe UTF-8 encoded strings."""
    try:
        return str(value).encode("utf-8", "ignore").decode("utf-8")
    except UnicodeDecodeError:
        return "Invalid Data"
def safe_str_value(value):
    return str(value) if value is not None else ""


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


from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import Table, TableStyle, Paragraph

def generate_incentive_caf_pdf(intention_data,
    data,
    customer_data, custom_profile=None, organization_profile=None
):
    """Generates a dynamic PDF for CAF Investment Details, using data from multiple models."""
    caf_reference_id = str(uuid.uuid4())  # Generate a unique reference ID

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    elements = []
    left_margin, right_margin = 50, 50
    start_height, line_height = 800, 18
    page_width, page_height = A4
    y_position = start_height
    is_first_page = [True]    
    def check_space(height_required):
        nonlocal y_position
        if y_position - height_required < 100:
            pdf.showPage()
            add_header()
            y_position = start_height - 3 * line_height
            return True
        return False

    def format_date(date_obj):
        return date_obj.strftime("%d/%m/%Y") if date_obj else ""

    def add_header():
        nonlocal y_position

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawRightString(page_width - right_margin, start_height, "MP Industrial Development Corporation Ltd.")
        pdf.setFont("Helvetica", 10)
        pdf.drawRightString(page_width - right_margin, start_height - 12, "21, Arera Hills, Bhopal, 462011")

        if is_first_page[0]:
            pdf.setFont("Helvetica-Bold", 12)
            text = "APPLICATION FORM FOR INCENTIVE"
            text_width = pdf.stringWidth(text, "Helvetica", 12)
            x_start = (page_width - text_width) / 2
            header_bottom = start_height - 4 * line_height
            pdf.drawString(x_start, header_bottom, text)
            pdf.line(x_start, header_bottom - 2, x_start + text_width + 3, header_bottom - 2)
            # move y_position **below** header title + gap
            y_position = header_bottom - 2 * line_height
            is_first_page[0] = False
        else:
            # On subsequent pages: draw simpler header, and start content a bit lower
            y_position = start_height - 3 * line_height

    
    # logo_url = os.path.join(settings.MEDIA_ROOT, 'MPIDC_Logo.jpg')
    # logo = ImageReader(logo_url)
    # pdf.drawImage(logo, left_margin, y_position - line_height - 60, width=150, height=150, mask='auto')
    logo_height = 0.8 * inch
    logo_width = 2.0 * inch

    logo_url = os.path.join(settings.MEDIA_ROOT, 'MPIDC_Logo.jpg')
    logo = ImageReader(logo_url)
    pdf.drawImage(
        logo,
        left_margin,
        y_position - line_height - logo_height,  # adjust Y to fit new size if needed
        width=logo_width,
        height=logo_height,
        mask='auto'
    )
    
    add_header()
    y_position -= 2 * line_height

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
            
    if data['caf_project']:
        def draw_blue_header(title):
            nonlocal y_position
            white_style = ParagraphStyle(
                name='WhiteText',
                parent=getSampleStyleSheet()['Normal'],
                textColor=colors.white,
                fontName='Helvetica-Bold',
                fontSize=10,
                leftIndent=5,
            )

            table = Table([[Paragraph(f"{title}", white_style)]], colWidths=[500])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            _, header_height = table.wrap(0,0)
            if y_position - header_height - 5 < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            y_position -= header_height
            table.drawOn(pdf, left_margin, y_position)
            y_position -= 5  # small gap below header

        def draw_section_table(section_data):
            nonlocal y_position
            table = Table(section_data, colWidths=[125, 125, 125, 125])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  # first column
                ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),  # third column

            ]))

            _, table_height = table.wrap(0,0)
            # Check if enough space, else add new page & header
            if y_position - table_height - 5 < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height


            y_position -= table_height
            table.drawOn(pdf, left_margin, y_position)
            y_position -= 5  # optional bottom gap

            if y_position < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height
                
        # Section 1: Organization Details
        field_style = ParagraphStyle(
        name="FieldStyle",
        fontName="Helvetica-Bold",
        fontSize=10,
        alignment=TA_LEFT,
        textColor=colors.black
        )

        draw_blue_header("Unit Details")
        table_data_1 = [
            [Paragraph("Intention Number", field_style), Paragraph(safe_str(intention_data.intention_id)),
            Paragraph("Name of Organization/Unit Name", field_style), Paragraph(safe_str(data['caf_project'].unit_name))],
            [Paragraph("Constitution of Unit", field_style), Paragraph(safe_str(data['caf_project'].constitution_type_name)),
            Paragraph("Type of unit", field_style), Paragraph(safe_str(data['caf_project'].unit_type))],
            [Paragraph("Date of Intention", field_style), Paragraph(format_date(data['caf_project'].date_of_intention)),
            Paragraph("Activity Type/Business Type", field_style), Paragraph(safe_str(data['caf_project'].activity_name))],
            [Paragraph("Sector", field_style), Paragraph(safe_str(data['caf_project'].sector_name)),
             Paragraph("", field_style), Paragraph("")],
        ]

        draw_section_table(table_data_1)
        y_position -= 20  

        # Section 2: Investment Details
        draw_blue_header("Project Details")
        unit_type = data['caf_project'].unit_type
        if unit_type == "New":
            table_data_2 = [
                [Paragraph("Commercial Production Date", field_style), Paragraph(format_date(data['incaf_investment'].comm_production_date)),
                Paragraph("Investment in Plant & Machinery (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].investment_in_plant_machinery))],
                [Paragraph("Investment in Building (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].investment_in_building)),
                Paragraph("Total Investment in Land", field_style), Paragraph(safe_str(data['incaf_investment'].total_investment_land))],            
                [Paragraph("Total Investment in Furniture and Fixture", field_style), Paragraph(safe_str(data['incaf_investment'].investment_furniture_fixtures)),
                '', ''],
                [Paragraph("Total Investment in Other Assets", field_style), Paragraph(safe_str(data['incaf_investment'].total_investment_other_asset)),
                Paragraph("Total Investment (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].total_investment_amount))],            
                [Paragraph("IEM Part A Number", field_style), Paragraph(safe_str(data['caf_project'].iem_a_number)),
                Paragraph("IEM Part A Date", field_style), Paragraph(format_date(data['caf_project'].iem_a_date))],
                [Paragraph("IEM Part B Number", field_style), Paragraph(safe_str(data['caf_project'].iem_b_number)),
                Paragraph("IEM Part B Date", field_style), Paragraph(format_date(data['caf_project'].iem_b_date))],
                [Paragraph("GST Number", field_style), Paragraph(safe_str(data['caf_project'].gstin)),
                Paragraph("Date of GST number issued", field_style), Paragraph(format_date(data['caf_project'].gstin_issue_date))],
                [Paragraph("Turnover as on COD", field_style), Paragraph(safe_str(data['incaf_investment'].turnover)),
                Paragraph("Whether the unit is an exporting unit?", field_style), Paragraph("Yes" if data['incaf_investment'].is_export_unit else "No")],
                [Paragraph("Is CCIP applicable?", field_style), Paragraph("Yes" if data['caf_project'].is_ccip else "No"),
                Paragraph("Foreign Direct Investment", field_style), Paragraph(safe_str(data['incaf_investment'].fdi_amount))],
                [Paragraph("Promoter’s equity (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].promoters_equity_amount)),
                Paragraph("Term loan (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].term_loan_amount))],
                [Paragraph("Total (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].total_finance_amount)),
                Paragraph("Is your company eligible for CSR?", field_style), Paragraph("Yes" if data['incaf_investment'].is_csr else "No")],
            ]
            if data['incaf_investment'].is_csr:
                table_data_2.append([
                    Paragraph("Average amount spent in the last three years (in lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].csr)),
                    Paragraph(""), Paragraph("")
                ])
        else:
            table_data_2 = [
                [Paragraph("Commercial Production Date", field_style), Paragraph(format_date(data['incaf_investment'].comm_production_date)),
                Paragraph("IEM Part A Number", field_style), Paragraph(safe_str(data['caf_project'].iem_a_number))],
                [Paragraph("IEM Part A Date", field_style), Paragraph(format_date(data['caf_project'].iem_a_date)),
                Paragraph("IEM Part B Number", field_style), Paragraph(safe_str(data['caf_project'].iem_b_number))],
                [Paragraph("IEM Part B Date", field_style), Paragraph(format_date(data['caf_project'].iem_b_date)),
                Paragraph("GST Number", field_style), Paragraph(safe_str(data['caf_project'].gstin))],
                [Paragraph("Date of GST number issued", field_style), Paragraph(format_date(data['caf_project'].gstin_issue_date)),
                Paragraph("Turnover as on COD", field_style), Paragraph(safe_str(data['incaf_investment'].turnover))],
                [Paragraph("Whether the unit is an exporting unit?", field_style), Paragraph("Yes" if data['incaf_investment'].is_export_unit else "No"),
                Paragraph("Is CCIP applicable?", field_style), Paragraph("Yes" if data['caf_project'].is_ccip else "No")],
                [Paragraph("Foreign Direct Investment", field_style), Paragraph(safe_str(data['incaf_investment'].fdi_amount)),
                Paragraph("Promoter’s equity (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].promoters_equity_amount))],
                [Paragraph("Term loan (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].term_loan_amount)),
                Paragraph("Total (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].total_finance_amount))],
                [Paragraph("Foreign Direct Investment (FDI) (in Lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].fdi_amount)),
                Paragraph("FDI Percentage", field_style), Paragraph(safe_str(data['incaf_investment'].fdi_percentage))],
                [Paragraph("Is your company eligible for CSR?", field_style), Paragraph("Yes" if data['incaf_investment'].is_csr else "No")],
            ]

            if data['incaf_investment'].is_csr:
                table_data_2.append([
                    Paragraph("Average amount spent in the last three years (in lakhs)", field_style), Paragraph(safe_str(data['incaf_investment'].csr)),
                    Paragraph(""), Paragraph("")
                ])

        draw_section_table(table_data_2)
        y_position -= 20  

        draw_blue_header("Land Details")
        # Get land_type and plot_type
        land_type = safe_str(data['caf_project'].land_type)
        plot_type = safe_str(data['caf_project'].plot_type)
        table_data_3 = []

        if land_type == "DIPIP (MPIDC)":
            if plot_type == "Developed":
                table_data_3 = [
                    [Paragraph("Type of Land", field_style), Paragraph(land_type),
                    Paragraph("Plot Type", field_style), Paragraph(plot_type)],
                    [Paragraph("District", field_style), Paragraph(safe_str(data['caf_project'].district_name)),
                    Paragraph("Regional Office", field_style), Paragraph(safe_str(data['caf_project'].regional_office_name))],
                    [Paragraph("DIPIP (MPIDC) Industrial Areas", field_style), Paragraph(safe_str(data['caf_project'].industrial_area_name)),
                    Paragraph("Block", field_style), Paragraph(safe_str(data['caf_project'].block_name))],
                    [Paragraph("Industrial Plot Number", field_style), Paragraph(safe_str(data['caf_project'].industrial_plot)),
                    Paragraph("Full Address of the Unit", field_style), Paragraph(safe_str(data['caf_project'].address_of_unit))],
                ]
            elif plot_type == "Undeveloped":
                table_data_3 = [
                    [Paragraph("Type of Land", field_style), Paragraph(land_type),
                    Paragraph("Plot Type", field_style), Paragraph(plot_type)],
                    [Paragraph("District", field_style), Paragraph(safe_str(data['caf_project'].district_name)),
                    Paragraph("Regional Office", field_style), Paragraph(safe_str(data['caf_project'].regional_office_name))],
                    [Paragraph("Block", field_style), Paragraph(safe_str(data['caf_project'].block_name)),
                    Paragraph("Full Address of the Unit", field_style), Paragraph(safe_str(data['caf_project'].address_of_unit))],
                ]

        elif land_type == "MSME":
            table_data_3 = [
                [Paragraph("Type of Land", field_style), Paragraph(land_type),
                Paragraph("District", field_style), Paragraph(safe_str(data['caf_project'].district_name))],
                [Paragraph("Regional Office", field_style), Paragraph(safe_str(data['caf_project'].regional_office_name)),
                Paragraph("MSME Industrial Areas", field_style), Paragraph(safe_str(data['caf_project'].industrial_area_name))],
                [Paragraph("Block", field_style), Paragraph(safe_str(data['caf_project'].block_name)),
                Paragraph("Industrial Plot Number", field_style), Paragraph(safe_str(data['caf_project'].industrial_plot))],
                [Paragraph("Full Address of the Unit", field_style), Paragraph(safe_str(data['caf_project'].address_of_unit)),
                Paragraph("", field_style), Paragraph("")],
            ]

        elif land_type == "Private Land":
            table_data_3 = [
                [Paragraph("Type of Land", field_style), Paragraph(land_type),
                Paragraph("District", field_style), Paragraph(safe_str(data['caf_project'].district_name))],
                [Paragraph("Regional Office", field_style), Paragraph(safe_str(data['caf_project'].regional_office_name)),
                Paragraph("Block", field_style), Paragraph(safe_str(data['caf_project'].block_name))],
                [Paragraph("Khasra Number", field_style), Paragraph(safe_str(data['caf_project'].industrial_plot)),
                Paragraph("Full Address of the Unit", field_style), Paragraph(safe_str(data['caf_project'].address_of_unit))],
            ]

        else:
            # Fallback for unknown land types
            table_data_3 = [
                [Paragraph("Type of Land", field_style), Paragraph(land_type),
                Paragraph("District", field_style), Paragraph(safe_str(data['caf_project'].district_name))],
                [Paragraph("Regional Office", field_style), Paragraph(safe_str(data['caf_project'].regional_office_name)),
                Paragraph("Block", field_style), Paragraph(safe_str(data['caf_project'].block_name))],
                [Paragraph("Industrial Plot Number", field_style), Paragraph(safe_str(data['caf_project'].industrial_plot)),
                Paragraph("Full Address of the Unit", field_style), Paragraph(safe_str(data['caf_project'].address_of_unit))],
            ]

        draw_section_table(table_data_3)
        y_position -= 20

        # Section 4: Contact Details
        draw_blue_header("Contact Details")
        table_data_4 = [
            [Paragraph("Name of Authorized Person", field_style), Paragraph(safe_str(data['caf_project'].contact_person_name)),
            Paragraph("Email", field_style), Paragraph(safe_str(data['caf_project'].contact_email))],
            [Paragraph("Mobile Number", field_style), Paragraph(safe_str(data['caf_project'].contact_mobile_no)),
            Paragraph("Landline", field_style), Paragraph(safe_str(data['caf_project'].contact_landline_no))],
            [Paragraph("Address of Registered Office", field_style),
            Paragraph(safe_str(data['caf_project'].company_address + " " + data['caf_project'].company_address_pincode)),
            Paragraph("Pin Code", field_style), Paragraph(safe_str(data['caf_project'].company_address_pincode))],
        ]
        draw_section_table(table_data_4)
        y_position -= 20  

    # Investment Details
        draw_blue_header("Investment Details")

        unit_type = safe_str(data['caf_project'].unit_type) or "Expansion"
        incaf_investment = data['incaf_investment']
        expansion_units = data.get('expansion_unit') or []

        if unit_type == 'New':
                # show short table for New
                expansion_table_data = [
                    [Paragraph("Investment in building (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.investment_in_building)),
                        Paragraph("Investment in Plant & machinery (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.investment_in_plant_machinery))],
                    [Paragraph("Investment in Furniture and Fixture (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.total_investment_other_asset)),
                        Paragraph("Total Investment (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.total_investment_amount))],
                ]
        elif unit_type in ["Expansion", "Diversification", "Expansion cum Diversification", "Technical Upgradation"]:

            total_building = (incaf_investment.investment_in_building_before_expansion or 0) + incaf_investment.investment_in_building
            total_pm = (incaf_investment.investment_in_plant_machinery_before_expansion or 0) + incaf_investment.investment_in_plant_machinery

            try:
                pm_building_percent = (
                    (incaf_investment.investment_in_building + incaf_investment.investment_in_plant_machinery) 
                    / (total_building + total_pm)
                ) * 100 if (total_building + total_pm) else 0
            except ZeroDivisionError:
                pm_building_percent = 0 

            expansion_table_data = [
                [Paragraph(f"Investment in land before {unit_type} (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.investment_land_before_expansion or 0)),
                Paragraph(f"Investment in land under {unit_type} (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.total_investment_land))],
                [Paragraph(f"Total investment in land (in Lakhs)", field_style),
                Paragraph(safe_str((incaf_investment.investment_land_before_expansion or 0) + incaf_investment.total_investment_land)),
                Paragraph(f"Investment in building before {unit_type} (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.investment_in_building_before_expansion or 0))],
                [Paragraph(f"Investment in building under {unit_type} (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.investment_in_building)),
                Paragraph(f"Total investment in building (in Lakhs)", field_style),
                Paragraph(safe_str((incaf_investment.investment_in_building_before_expansion or 0) + incaf_investment.investment_in_building))],
                [Paragraph(f"Investment in plant & machinery before {unit_type} (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.investment_in_plant_machinery_before_expansion or 0)),
                Paragraph(f"Investment in plant & machinery under {unit_type} (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.investment_in_plant_machinery))],
                [Paragraph(f"Total investment in plant & machinery (in Lakhs)", field_style),
                Paragraph(safe_str((incaf_investment.investment_in_plant_machinery_before_expansion or 0) + incaf_investment.investment_in_plant_machinery)),
                Paragraph(f"Investment in Other Assets before {unit_type} (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.investment_other_asset_before_expansion or 0))],
                [Paragraph(f"Investment in Other Assets under {unit_type} (in Lakhs)", field_style), Paragraph(safe_str(incaf_investment.total_investment_other_asset)),
                Paragraph(f"Total investment in Other Assets (in Lakhs)", field_style),
                Paragraph(safe_str((incaf_investment.investment_other_asset_before_expansion or 0) + incaf_investment.total_investment_other_asset))],

            [Paragraph(f"Total investment before {unit_type} (in Lakhs)", field_style),
            Paragraph(safe_str(
                (incaf_investment.total_investment_amount_before_expansion)
            )),
            Paragraph(f"Total investment under {unit_type} (in Lakhs)", field_style),
            Paragraph(safe_str(
                incaf_investment.total_investment_amount
            ))],

            [
                Paragraph("Total investment (in Lakhs)", field_style),
                Paragraph(safe_str(
                    (incaf_investment.total_investment_amount_before_expansion or 0) + 
                    (incaf_investment.total_investment_amount or 0)
                ), styleN),
                Paragraph(f"% of Building and Plant & Machinery under {unit_type}", field_style),
                Paragraph(f"{round(pm_building_percent, 2)} %", styleN)
            ]
        ]

        if y_position - (len(expansion_table_data) * 15) < 100:
            pdf.showPage()
            add_header()
            y_position = start_height - 3 * line_height

        expansion_table = Table(expansion_table_data, colWidths=[125, 125, 125, 125])
        expansion_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),             
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        table_width, table_height = expansion_table.wrapOn(pdf, left_margin, y_position)
        expansion_table.drawOn(pdf, left_margin, y_position - table_height)
        y_position -= table_height + 30

        if y_position < 100:
            pdf.showPage()
            add_header()
            y_position = start_height - 3 * line_height

    if data['incaf_power']:
        # Prepare section header
        blue_row_data = [["Power Details"]]
        blue_row_table = Table(blue_row_data, colWidths=[500])
        blue_row_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        # Measure header height
        _, header_height = blue_row_table.wrap(0, 0)

        # Check if enough space; if not, add new page and header
        if y_position - header_height - 10 < 100:
            pdf.showPage()
            add_header()  # add header also resets y_position
        # draw header at current y_position - header_height
        blue_row_table.drawOn(pdf, left_margin, y_position - header_height)
        y_position -= header_height + 10  # update y_position

        # Prepare power data
        incaf_power = data['incaf_power']
        incaf_power_load = data['incaf_power_load'].first() 
        unit_type = data['caf_project'].unit_type
        power_table_data = []
        if unit_type == "New":

            power_table_data = [
                [Paragraph("Type of Connection", field_style), Paragraph(safe_str(incaf_power.connection_type)), 
                Paragraph("Date of Connection", field_style), Paragraph(format_date(incaf_power.date_of_connection))], 
                [Paragraph("Power load (in KVA)", field_style), Paragraph(safe_str(incaf_power.load_consumption)), 
                Paragraph("Date of Enhancement of Load", field_style), Paragraph(safe_str(incaf_power.enhancement_load_date))],         
            ]

        elif unit_type in ["Expansion", "Diversification", "Expansion cum Diversification", "Technical Upgradation"]:
            label = data['caf_project'].unit_type
            power_table_data.extend([
                [Paragraph(f"Type of Connection {label}", field_style), Paragraph(safe_str(incaf_power.connection_type)),
                Paragraph(f"Power load Before {label} (in KVA)", field_style), Paragraph(safe_str(incaf_power.power_load_before_expansion))],
                [Paragraph(f"Date of Connection {label}", field_style), Paragraph(format_date(incaf_power.date_of_connection)),
                Paragraph("Date of Enhancement of Load", field_style), Paragraph(safe_str(incaf_power.enhancement_load_date))],
                [Paragraph("Power load after (in KVA)", field_style), Paragraph(safe_str(incaf_power.load_consumption)),
                '', ''],
            ])

        if data.get('incaf_power_load'):
            for pl in data['incaf_power_load']:
                power_table_data.append([
                    Paragraph("Supplementary Sanction Load (KVA)", field_style), Paragraph(safe_str(pl.supplementary_load)),
                    Paragraph("Supplementary Sanction Load Date", field_style), Paragraph(format_date(pl.supplementary_load_date))
                ])

        if data.get('incaf_submeter'):
            for sm in data['incaf_submeter']:
                power_table_data.append([
                    Paragraph("Meter Number", field_style), Paragraph(safe_str(sm.meter_number)),
                ])

        # Build power table
        power_table = Table(power_table_data, colWidths=[125, 125, 125, 125])
        power_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey), 
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        # Measure table height
        _, table_height = power_table.wrap(0, 0)

        # Check space again
        if y_position - table_height - 10 < 100:
            pdf.showPage()
            add_header()

        # draw table at y_position - table_height
        power_table.drawOn(pdf, left_margin, y_position - table_height)
        y_position -= table_height + 10  # update y_position

        # After table, if very low again, add new page to be ready for next block
        if y_position < 100:
            pdf.showPage()
            add_header()

    # if data.get('incaf_power_load'):
    #     blue_row_data = [["Supplementary Power Load Details"]]
    #     blue_row_table = Table(blue_row_data, colWidths=[500])
    #     blue_row_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
    #         ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
    #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #         ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
    #         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    #     ]))

    #     # Get related power load data
    #     power_loads = data['incaf_power_load'].all()

    #     if not power_loads:
    #         power_load_table_data = [["No supplementary power load details available", ""]]
    #     else:
    #         power_load_table_data = [["Supplementary Load", "Supplementary Load Date"]]
    #         for load in power_loads:
    #             power_load_table_data.append([
    #                 safe_str(load.supplementary_load),
    #                 format_date(load.supplementary_load_date)
    #             ])

    #     power_load_table = Table(power_load_table_data, colWidths=[250, 250])
    #     power_load_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    #         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    #         ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    #         ('FONTSIZE', (0, 0), (-1, -1), 10),
    #         ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    #     ]))

    #     _, header_height = blue_row_table.wrap(0, 0)
    #     _, table_height = power_load_table.wrap(0, 0)
    #     required_height = header_height + 10 + table_height + 10

    #     if y_position - required_height < 100:
    #         pdf.showPage()
    #         add_header()

    #     blue_row_table.drawOn(pdf, left_margin, y_position - header_height)
    #     y_position -= header_height + 10
    #     power_load_table.drawOn(pdf, left_margin, y_position - table_height)
    #     y_position -= table_height + 10

    #     if y_position < 100:
    #         pdf.showPage()
    #         add_header()

    # if data['incaf_submeter'].all():
    #     blue_row_data = [["Sub Meter Details"]]
    #     blue_row_table = Table(blue_row_data, colWidths=[500])
    #     blue_row_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
    #         ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
    #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #         ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
    #         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    #     ]))

    #     _, header_height = blue_row_table.wrap(0, 0)
    #     check_space(header_height + 10)  
    #     y_position -= header_height
    #     blue_row_table.drawOn(pdf, left_margin, y_position)
    #     y_position -= 10  

    #     sub_meters = data['incaf_submeter'].all()

    #     if not sub_meters:
    #         sub_meter_table_data = [["No sub meter details available"]]
    #     else:
    #         sub_meter_table_data = [["Meter Number"]]
    #         for sub_meter in sub_meters:
    #             sub_meter_table_data.append([
    #                 safe_str(sub_meter.meter_number)
    #             ])

    #     # Create sub meter table
    #     sub_meter_table = Table(sub_meter_table_data, colWidths=[500])
    #     sub_meter_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    #         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    #         ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    #         ('FONTSIZE', (0, 0), (-1, -1), 10),
    #         ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    #     ]))

    #     _, table_height = sub_meter_table.wrap(0, 0)
    #     check_space(table_height + 10)
    #     y_position -= table_height
    #     sub_meter_table.drawOn(pdf, left_margin, y_position)
    #     y_position -= 10  

    #     if y_position < 100:
    #         pdf.showPage()
    #         add_header()
    #         y_position = start_height - 3 * line_height
            
    # Employment Details
    if data.get('incaf_employment'):
        blue_row_data = [["Employment Details"]]
        blue_row_table = Table(blue_row_data, colWidths=[500])
        blue_row_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        cell_style = ParagraphStyle('cell', fontName='Helvetica', fontSize=10, leading=12)
        incaf_employment = data['incaf_employment']
        employment_table_data = []
        if data['caf_project'].unit_type in ["Expansion", "Diversification", "Expansion cum Diversification", "Technical Upgradation"]:
            unit_type_label = data['caf_project'].unit_type
            employment_table_data.extend([
                [Paragraph(f"No. of employees bonafide residence in MP Before {unit_type_label}", field_style), Paragraph(safe_str(incaf_employment.employee_from_mp_before_expansion), cell_style),
                 Paragraph(f"Number of employees outside of MP Before {unit_type_label}", field_style), Paragraph(safe_str(incaf_employment.employees_outside_mp_before_expansion), cell_style)],
                [Paragraph(f"Total number of employees Before {unit_type_label}", field_style), Paragraph(safe_str(incaf_employment.total_employee_before_expansion), cell_style),
                 Paragraph(f"% of MP Domicile Before {unit_type_label}", field_style), Paragraph(safe_str(incaf_employment.employee_domicile_percentage_before_expansion), cell_style)],
            ])
        # Prepare Employment Table Data
        employment_table_data.extend([
            [Paragraph("No. of employees bonafide residence in MP", field_style), Paragraph(safe_str(incaf_employment.employees_from_mp), cell_style),
            Paragraph("Number of employees outside of MP", field_style), Paragraph(safe_str(incaf_employment.employees_outside_mp), cell_style)],
            [Paragraph("Total number of employees", field_style), Paragraph(safe_str(incaf_employment.total_employee), cell_style),
            Paragraph("% of MP Domicile", field_style), Paragraph(safe_str(incaf_employment.employee_domicile_percentage), cell_style)],
            [Paragraph("No. of Differently Abled Employees", field_style), Paragraph(safe_str(incaf_employment.number_of_differently_abled_employees), cell_style),
            Paragraph("% of Differently Abled Employees", field_style), Paragraph(safe_str(incaf_employment.percentage_of_differently_abled_employees), cell_style)],
          
        ])

        employment_table = Table(employment_table_data, colWidths=[125, 125, 125, 125])
        employment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),   
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        _, header_height = blue_row_table.wrap(0, 0)
        _, table_height = employment_table.wrap(0, 0)
        required_height = header_height + 10 + table_height + 10

        if y_position - required_height < 100:
            pdf.showPage()
            add_header()

        blue_row_table.drawOn(pdf, left_margin, y_position - header_height)
        y_position -= header_height + 10
        employment_table.drawOn(pdf, left_margin, y_position - table_height)
        y_position -= table_height + 10

        if y_position < 100:
            pdf.showPage()
            add_header()

    if data['incaf_incentive']:
        # Add Section Title (Blue Row)
        incaf_incentive = data['incaf_incentive']
        incentive_data = incaf_incentive.incentive_json or {}
        blue_row_data = [["Incentive Details"]]
        blue_row_table = Table(blue_row_data, colWidths=[500])
        blue_row_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        table_width, header_height = blue_row_table.wrap(0, 0)
        if y_position - header_height - 10 < 100:
            pdf.showPage()
            add_header()
            y_position = start_height - 3 * line_height

        blue_row_table.drawOn(pdf, left_margin, y_position - header_height)
        y_position -= header_height + 15

        if bool(incentive_data.get("is_ipp")):
            sub_header_data = [["Investment Promotion Assistance"]]
            sub_header_table = Table(sub_header_data, colWidths=[500])
            sub_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#D9D9D9")),  # Light grey
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            table_width, sub_header_height = sub_header_table.wrap(0, 0)
            if y_position - sub_header_height < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            sub_header_table.drawOn(pdf, left_margin, y_position - sub_header_height)
            y_position -= sub_header_height + 10   

            ipa_table_data = [
                [Paragraph("First Purchase Date", field_style), Paragraph(safe_str_value(incentive_data.get("first_purchase_date"))),
                Paragraph("First Sales Date", field_style), Paragraph(safe_str_value(incentive_data.get("first_sales_date")))],
                [Paragraph("Commercial Operation Date", field_style), Paragraph(safe_str_value(incentive_data.get("comm_proudction_date"))),
                Paragraph("1st claim year (Current year / Next year)", field_style), Paragraph(safe_str_value(incentive_data.get("incentive_year")))],
                [Paragraph("Investment in building (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get('investment_in_building', ''))),
                Paragraph("Investment in Plant & machinery (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get('investment_in_plant_machinery', '')))],
                [Paragraph("Investment in in-House R & D (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get('investment_in_house', ''))),
                Paragraph("Investment in Captive power (Renewable energy) (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get('investment_captive_power', '')))],
                [Paragraph("Investment in Energy saving Devices (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get('investment_energy_saving_devices', ''))),
                Paragraph("Investment in cost of imported second hand machinery", field_style), Paragraph(safe_str_value(incentive_data.get('investment_imported_second_hand_machinery', '')))],
                [Paragraph("Investment in cost of refurbishment(if any) (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get('investment_refurbishment', ''))), 
                Paragraph("Total Investment (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get('total_investment', '')))],

            ]

            table_height_estimate = len(ipa_table_data) * 20 + 20
            if y_position - table_height_estimate < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            incentive_table = Table(ipa_table_data, colWidths=[125, 125, 125, 125])
            incentive_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
                ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),  
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            table_width, actual_table_height = incentive_table.wrap(0, 0)
            incentive_table.drawOn(pdf, left_margin, y_position - actual_table_height)
            y_position -= actual_table_height + 30

            if y_position < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

        if bool(incentive_data.get("is_efs")):
            sub_header_data = [["Export Freight Subsidy"]]
            sub_header_table = Table(sub_header_data, colWidths=[500])
            sub_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#D9D9D9")),  
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            table_width, sub_header_height = sub_header_table.wrap(0, 0)
            if y_position - sub_header_height < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            sub_header_table.drawOn(pdf, left_margin, y_position - sub_header_height)
            y_position -= sub_header_height + 10

            ipa_table_data = [
                [Paragraph("Products / Goods being transported for exports.", field_style), Paragraph(safe_str_value(incentive_data.get("goods_transport"))),
                Paragraph("The mode of Transportation of goods (Air ,Rail, Road)", field_style), Paragraph(safe_str_value(incentive_data.get("mode_transportation")))],
                [Paragraph("Distance between the location of the unit and the port/air cargo facility/international broker (Distance in KM)", field_style), 
                 Paragraph(safe_str_value(incentive_data.get("distance_location_unit"))),
                '', ''],

            ]

            table_height_estimate = len(ipa_table_data) * 20 + 20
            if y_position - table_height_estimate < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            incentive_table = Table(ipa_table_data, colWidths=[125, 125, 125, 125])
            incentive_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
                ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),   
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            table_width, actual_table_height = incentive_table.wrap(0, 0)
            incentive_table.drawOn(pdf, left_margin, y_position - actual_table_height)
            y_position -= actual_table_height + 30

            if y_position < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

        if bool(incentive_data.get("is_ipr")):
            sub_header_data = [["Assistance for Intellectual Property Rights (IPR)"]]
            sub_header_table = Table(sub_header_data, colWidths=[500])
            sub_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#D9D9D9")),  # Light grey
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            table_width, sub_header_height = sub_header_table.wrap(0, 0)
            if y_position - sub_header_height < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            sub_header_table.drawOn(pdf, left_margin, y_position - sub_header_height)
            y_position -= sub_header_height + 10            
            ipa_table_data = [
                [Paragraph("Details of IPR applied for", field_style), Paragraph(safe_str_value(incentive_data.get("detail_ipr"))),
                Paragraph("Date of obtaining IPR.", field_style), Paragraph(safe_str_value(incentive_data.get("date_ipr")))],
                [Paragraph("Fee paid for acquisition of IPR (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("fee_paid_ipr"))),
                Paragraph("Amount Claimed (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("ipr_type")))],
                [Paragraph("Type of IPR", field_style),
                    Paragraph(", ".join(incentive_data.get("ipr_type", [])) if incentive_data.get("ipr_type") else ""),
                    "", ""
                ]
            ]

            table_height_estimate = len(ipa_table_data) * 20 + 20
            if y_position - table_height_estimate < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            incentive_table = Table(ipa_table_data, colWidths=[125, 125, 125, 125])
            incentive_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
                ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),  
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            table_width, actual_table_height = incentive_table.wrap(0, 0)
            incentive_table.drawOn(pdf, left_margin, y_position - actual_table_height)
            y_position -= actual_table_height + 30

            if y_position < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

        if bool(incentive_data.get("is_gia")):
            sub_header_data = [["Green Industrialization"]]
            sub_header_table = Table(sub_header_data, colWidths=[500])
            sub_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#D9D9D9")),  # Light grey
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            table_width, sub_header_height = sub_header_table.wrap(0, 0)
            if y_position - sub_header_height < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            sub_header_table.drawOn(pdf, left_margin, y_position - sub_header_height)
            y_position -= sub_header_height + 10

            ipa_table_data = [
                [Paragraph("Type of Waste Management System", field_style), Paragraph(safe_str_value(incentive_data.get("type_of_wms"))),
                Paragraph("Total Expenditure on Waste Management System (in Lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("wms_total_expenditure")))],
            ]

            table_height_estimate = len(ipa_table_data) * 20 + 20
            if y_position - table_height_estimate < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            incentive_table = Table(ipa_table_data, colWidths=[125, 125, 125, 125])
            incentive_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
                ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),   
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            table_width, actual_table_height = incentive_table.wrap(0, 0)
            incentive_table.drawOn(pdf, left_margin, y_position - actual_table_height)
            y_position -= actual_table_height + 30

            if y_position < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

        if bool(incentive_data.get("is_id")):
            sub_header_data = [["Infrastructure Development"]]
            sub_header_table = Table(sub_header_data, colWidths=[500])
            sub_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#D9D9D9")),  # Light grey
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            table_width, sub_header_height = sub_header_table.wrap(0, 0)
            if y_position - sub_header_height < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            sub_header_table.drawOn(pdf, left_margin, y_position - sub_header_height)
            y_position -= sub_header_height + 10            

            ipa_table_data = [
                [Paragraph("Road Expenditure (in lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("ida_road"))),
                Paragraph("Water Expenditure (in lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("wms_expenditure")))],
                [Paragraph("Power Expenditure (in lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("power_expenditure"))),
                Paragraph("Gas Pipeline Expenditure (in lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("gas_expenditure")))],
                [Paragraph("Drainage Expenditure (in lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("drainage_expenditure"))),
                Paragraph("Sewage Expenditure (in lakhs)", field_style), Paragraph(safe_str_value(incentive_data.get("sewage_expenditure")))],
            ]

            table_height_estimate = len(ipa_table_data) * 20 + 20
            if y_position - table_height_estimate < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            incentive_table = Table(ipa_table_data, colWidths=[125, 125, 125, 125])
            incentive_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
                ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),   
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),                
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            table_width, actual_table_height = incentive_table.wrap(0, 0)
            incentive_table.drawOn(pdf, left_margin, y_position - actual_table_height)
            y_position -= actual_table_height + 30

            if y_position < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

        if bool(incentive_data.get("is_mandifee")):
            sub_header_data = [["Mandi Fee Reimbursement"]]
            sub_header_table = Table(sub_header_data, colWidths=[500])
            sub_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#D9D9D9")),  # Light grey
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            table_width, sub_header_height = sub_header_table.wrap(0, 0)
            if y_position - sub_header_height < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            sub_header_table.drawOn(pdf, left_margin, y_position - sub_header_height)
            y_position -= sub_header_height + 10

            ipa_table_data = [
                [Paragraph("Licenese No.", field_style), Paragraph(safe_str_value(incentive_data.get("mandi_license"))),
                Paragraph("Issue Date", field_style), Paragraph(safe_str_value(incentive_data.get("mandi_license_date")))],
            ]

            table_height_estimate = len(ipa_table_data) * 20 + 20
            if y_position - table_height_estimate < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

            incentive_table = Table(ipa_table_data, colWidths=[125, 125, 125, 125])
            incentive_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
                ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),   
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),                
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            table_width, actual_table_height = incentive_table.wrap(0, 0)
            incentive_table.drawOn(pdf, left_margin, y_position - actual_table_height)
            y_position -= actual_table_height + 30

            if y_position < 100:
                pdf.showPage()
                add_header()
                y_position = start_height - 3 * line_height

    if data['incaf_products'].all():
        unit_type = safe_str(data['caf_project'].unit_type) or "New"
        heading_text = "Product Details"
        sub_heading_text = None   
        table_headers = []
        product_table_data = []
        cell_style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=9, wordWrap='CJK')

        products = data['incaf_products'].all()

        if unit_type in ["New", "Diversification"]:
            # heading_text = "Product Details"
            table_headers = ["Product Name", "Total Annual Capacity", "Unit"]
            product_table_data = [
                [Paragraph(safe_str(p.product_name), cell_style),
                Paragraph(safe_str(p.total_annual_capacity), cell_style),
                Paragraph(safe_str(p.measurement_unit_name or p.other_measurement_unit_name), cell_style)]
                for p in products
            ]

        elif unit_type == "Expansion":
            sub_heading_text = "Annual Capacity Before Expansion"
            table_headers = [
                "Product Name", "As per IEM", "As per average of last 3 years production",
                "Annual Capacity During Expansion", "Total Annual Capacity", "Unit"
            ]
            product_table_data = [
                [Paragraph(safe_str(p.product_name), cell_style),
                Paragraph(safe_str(p.ime_before_expansion), cell_style),
                Paragraph(safe_str(p.avg_production_before_expansion), cell_style),
                Paragraph(safe_str(p.annual_capacity_before_expansion), cell_style),
                Paragraph(safe_str(p.total_annual_capacity), cell_style),
                Paragraph(safe_str(p.measurement_unit_name or p.other_measurement_unit_name), cell_style)]
                for p in products
            ]

        elif unit_type == "Expansion cum Diversification":
            sub_heading_text = "Annual Capacity Before Expansion cum Diversification"
            table_headers = [
                "Product Name", "As per IEM", "As per average of last 3 years production",
                "Annual Capacity During Expansion cum Diversification", "Total Annual Capacity", "Unit"
            ]
            product_table_data = [
                [Paragraph(safe_str(p.product_name), cell_style),
                Paragraph(safe_str(p.ime_before_expansion), cell_style),
                Paragraph(safe_str(p.avg_production_before_expansion), cell_style),
                Paragraph(safe_str(p.annual_capacity_before_expansion), cell_style),
                Paragraph(safe_str(p.total_annual_capacity), cell_style),
                Paragraph(safe_str(p.measurement_unit_name or p.other_measurement_unit_name), cell_style)]
                for p in products
            ]

        elif unit_type == "Technical Upgradation":
            sub_heading_text = "Annual Capacity Before Technical Upgradation"
            table_headers = ["Product Name", "Existing Capacity", "Capacity after Technical Upgradation", "Unit"]
            product_table_data = [
                [Paragraph(safe_str(p.product_name), cell_style),
                Paragraph(safe_str(p.avg_production_before_expansion), cell_style),
                Paragraph(safe_str(p.annual_capacity_before_expansion), cell_style),
                Paragraph(safe_str(p.measurement_unit_name or p.other_measurement_unit_name), cell_style)]
                for p in products
            ]

        else:
            # heading_text = "Product Details"
            table_headers = ["Product Name", "Total Annual Capacity", "Unit"]
            product_table_data = [
                [Paragraph(safe_str(p.product_name), cell_style),
                Paragraph(safe_str(p.total_annual_capacity), cell_style),
                Paragraph(safe_str(p.measurement_unit_name or p.other_measurement_unit_name), cell_style)]
                for p in products
            ]

        # Insert heading before table
        blue_row_data = [[heading_text]]
        blue_row_table = Table(blue_row_data, colWidths=[500])
        blue_row_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        _, header_height = blue_row_table.wrap(0, 0)
        check_space(header_height + 10)
        y_position -= header_height
        blue_row_table.drawOn(pdf, left_margin, y_position)
        y_position -= 10

        if sub_heading_text:
            sub_row_data = [[sub_heading_text]]
            sub_row_table = Table(sub_row_data, colWidths=[500])
            sub_row_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#4a90e2")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            _, sub_header_height = sub_row_table.wrap(0, 0)
            check_space(sub_header_height + 10)
            y_position -= sub_header_height
            sub_row_table.drawOn(pdf, left_margin, y_position)
            y_position -= 15   

        # Compose final table: single header row + product rows
        header_row = [Paragraph(h, ParagraphStyle(name='Header', fontName='Helvetica-Bold', fontSize=9, wordWrap='CJK')) for h in table_headers]
        final_table_data = [header_row] + product_table_data

        # Adjust colWidths smartly
        if len(table_headers) == 6:  # e.g. Expansion types
            col_widths = [80, 60, 90, 90, 90, 80]
        elif len(table_headers) == 4:  # Technical Upgradation
            col_widths = [150, 100, 150, 100]
        else:  # default 3 cols
            col_widths = [200, 150, 150]

        product_table = Table(final_table_data, colWidths=col_widths)
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        _, table_height = product_table.wrap(0, 0)
        check_space(table_height + 10)
        y_position -= table_height
        product_table.drawOn(pdf, left_margin, y_position)
        y_position -= 10

        if y_position < 100:
            pdf.showPage()
            add_header()
            y_position = start_height - 3 * line_height

    if custom_profile:
        user_header = Table([["User Details"]], colWidths=[500])
        user_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        _, header_height = user_header.wrap(0, 0)
        check_space(header_height + 10) 
        y_position -= header_height
        user_header.drawOn(pdf, left_margin, y_position)
        y_position -= 10  

        profile_data = [
            [Paragraph("Full Name", field_style), Paragraph(safe_str(custom_profile.name))],
            [Paragraph("Phone Number", field_style), Paragraph(safe_str(custom_profile.mobile_no))],
            [Paragraph("Email", field_style), Paragraph(safe_str(custom_profile.email))],
            [Paragraph("Designation", field_style), Paragraph(safe_str(custom_profile.designation))],
            [Paragraph("Alternate Email", field_style), Paragraph(safe_str(custom_profile.alternate_email_id))],
            [Paragraph("PAN Card Number", field_style), Paragraph(safe_str(custom_profile.pan_card_number))],
            [Paragraph("PAN Verify", field_style), Paragraph(safe_str(custom_profile.pan_verify))],
        ]

        if custom_profile.dob:
            profile_data.insert(2, [Paragraph("Date of Birth", field_style), format_date(custom_profile.dob)])

        profile_table = Table(profile_data, colWidths=[250, 250])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),   
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))

        _, table_height = profile_table.wrap(0, 0)
        check_space(table_height + 10)
        y_position -= table_height
        profile_table.drawOn(pdf, left_margin, y_position)
        y_position -= 10  

        if y_position < 100:
            pdf.showPage()
            add_header()
            y_position = start_height - 3 * line_height

    if organization_profile:
        org_header = Table([["Promoter/MD Information"]], colWidths=[500])
        org_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1669ae")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        # Measure header height
        _, header_height = org_header.wrap(0, 0)
        check_space(header_height + 10)
        org_header.drawOn(pdf, left_margin, y_position - header_height)
        y_position -= header_height + 10

        org_data = [
            [Paragraph("Name", field_style), Paragraph(safe_str(organization_profile.name))],
            [Paragraph("Mobile Number", field_style), Paragraph(safe_str(organization_profile.mobile_number))],
            [Paragraph("Designation", field_style), Paragraph(safe_str(organization_profile.designation))],
            [Paragraph("Email", field_style), Paragraph(safe_str(organization_profile.email_id))],
        ]

        org_table = Table(org_data, colWidths=[250, 250])
        org_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),   
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),   
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))

        _, table_height = org_table.wrap(0, 0)
        check_space(table_height + 10)
        y_position -= table_height
        org_table.drawOn(pdf, left_margin, y_position)
        y_position -= 10  

        if y_position < 100:
            pdf.showPage()
            add_header()
            y_position = start_height - 3 * line_height

    bottom_margin = 50
    line_height = 14

    # Draw the affirmation text first, wrapped if long
    affirm_text = "I/We further solemnly affirm that the mentioned declaration is correct to the best of my/our knowledge and belief and no fact has been suppressed in this connection."
    pdf.setFont("Helvetica", 11)

    text_width = page_width - left_margin - right_margin
    wrapped_lines = []
    current_line = ""
    for word in affirm_text.split():
        test_line = current_line + " " + word if current_line else word
        if pdf.stringWidth(test_line, "Helvetica", 11) < text_width:
            current_line = test_line
        else:
            wrapped_lines.append(current_line)
            current_line = word
    if current_line:
        wrapped_lines.append(current_line)

    # Estimate height needed
    needed_height = len(wrapped_lines) * line_height

    # Check space
    if y_position - needed_height < bottom_margin:
        pdf.showPage()
        add_header()
        y_position = start_height - 3 * line_height

    # Draw wrapped lines
    for line in wrapped_lines:
        pdf.drawString(left_margin, y_position, line)
        y_position -= line_height

    # Then "Thanking you,"
    pdf.drawString(left_margin, y_position, "Thanking you,")
    y_position -= 2 * line_height    

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(left_margin, y_position, "Place: Bhopal")
    pdf.drawString(400, y_position, f"Investor Name: {safe_str(customer_data.name)}")
    pdf.drawString(left_margin, y_position - line_height, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    pdf.drawString(400, y_position - line_height, f"Mobile No: {safe_str(customer_data.mobile_no)}")
    pdf.drawString(400, y_position - 2 * line_height, f"Email ID: {safe_str(customer_data.email)}")

    # Done
    pdf.save()
    buffer.seek(0)

    # Ensure the directory exists
    pdf_directory = os.path.join(settings.MEDIA_ROOT, "incentive_caf_pdfs")
    os.makedirs(pdf_directory, exist_ok=True)

    file_name = f"caf_{data['caf_project'].caf_id}_{caf_reference_id}.pdf"
    file_path = os.path.join(pdf_directory, file_name)
    
    with open(file_path, "wb") as f:
        f.write(buffer.getvalue())

    with open(file_path, "rb") as file_to_upload:
        doc_file = SimpleUploadedFile(
            name=file_name,
            content=file_to_upload.read(),
            content_type="application/pdf"
        )

    documents = [{
        "file": doc_file,
        "file_name": doc_file.name,
        "file_type": doc_file.content_type
    }]

    document_folder = customer_data.document_folder if customer_data.document_folder else customer_data.user_id
    url = settings.MINIO_API_HOST + "/minio/uploads"

    upload_response = upload_files_to_minio(documents, url, document_folder)

    if not upload_response["success"]:
        return Response({
            "status": False,
            "message": "File upload failed",
            "error": upload_response["error"],
            "server_response": upload_response["response"]
        }, status=500)


    file_url = f"{settings.MEDIA_URL}incentive_caf_pdfs/{file_name}"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)            

    except Exception as e:
        return Response({
            "status":False,
            "message":global_err_message
        },status=500)

    # Save to database
    caf_pdf, created = IncentiveCAF.objects.update_or_create(
        id=data['caf_project'].caf_id,
        defaults={
            "caf_pdf_url": upload_response['data'][0]["path"]
        },
    )
    

    return upload_response['data'][0]["path"]

class IncentiveAuditLogMixin:
    def create_incentive_audit_log(
        self,
        caf_instance,
        module,
        user_name=None,
        user_role=None,
        action_type=None,
        old_value=None,
        new_value=None,
    ):
        try:
            IncentiveAuditLog.objects.create(
                caf=caf_instance,
                module=module,
                user_name=user_name,
                user_role=user_role,
                action_type=action_type,
                old_value=old_value,
                new_value=new_value,
            )
            return None 
        except Exception as e:
            logger.error(global_err_message, exc_info=True)
            return Response(
                {
                    "status": False,
                    "message": "Error while creating incentive audit log",
                    "error": global_err_message,
                    "data": {},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class IncentiveApprovalMixin:
    def create_incentive_approval_log(self, *args, **kwargs):
        try:
            IncentiveApprovalHistory.objects.create(
                caf=kwargs['caf'],
                next_approver_designation=kwargs['next_approval_role'],
                incentive_action = kwargs['action'],
                approving_document = kwargs['document_path'],
                approving_remark = kwargs['remark'],
                name_of_authority = kwargs['user_name'],
                authority_designation = kwargs['user_designation'],
                sla_days = kwargs['sla_days'],
                sla_due_date = kwargs['sla_due_date'],
                is_overdue = kwargs['is_overdue'] if 'is_overdue' in kwargs else False,
                resolved_at = kwargs['resolved_at'] if 'resolved_at' in kwargs else None
            )
            return True 
        except Exception as e:
            logger.error(global_err_message, exc_info=True)
            return Response(
                {
                    "status": False,
                    "message": "Error while creating approval history log",
                    "error": global_err_message,
                    "data": {},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

def get_sla_date(sla_days):
    today = date.today()
    sla_due_date = today + timedelta(days=sla_days)
    return sla_due_date

from datetime import date, datetime

def format_date(value):
    """Safely format a date/datetime to 'DD-MM-YYYY', return '' if invalid."""
    if not value:
        return ""
    
    if isinstance(value, (date, datetime)):
        return value.strftime("%d-%m-%Y")
    
    # If it's a string, try parsing
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed.strftime("%d-%m-%Y")
        except ValueError:
            return value  # Return as-is if it's not a valid date string
    
    # If it's not a date (like Decimal), just return as string
    return str(value)

def generate_agenda_pdf(agenda_data, products_data, user_profile, existing_agenda_incentive):
    buffer = io.BytesIO()
    page_width, page_height = A4
    styles = getSampleStyleSheet()
    custom_styles = {}
    custom_styles['CustomTitle'] = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.darkblue,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    custom_styles['CustomHindi'] = ParagraphStyle(
        'CustomHindi',
        parent=styles['Normal'],
        fontName='NotoSansDevanagari-Regular',
        fontSize=12,
        leading=16,
        textColor=colors.black
    )

    field_style = ParagraphStyle('FieldLabel', fontName='Helvetica-Bold', fontSize=10, alignment=TA_JUSTIFY)
    value_style = ParagraphStyle('FieldValue', fontName='Helvetica', fontSize=10, alignment=TA_JUSTIFY)

    def safe_str(value):
        if value is None:
            return ""
        if isinstance(value, (date, datetime)):
            return value.strftime("%d/%m/%Y")
        return str(value)

    def format_date(dt):
        if not dt:
            return ""
        if isinstance(dt, str):
            try:
                d = datetime.strptime(dt, "%Y-%m-%d")
                return d.strftime("%d/%m/%Y")
            except Exception:
                return dt
        return dt.strftime("%d/%m/%Y")

    def safe_str_value(val):
        if val is None:
            return ""
        if isinstance(val, bytes):
            return val.decode("utf-8", errors="ignore")
        return str(val)


    story = []

    right_style = ParagraphStyle(
        name='RightAligned',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
        fontSize=10
    )

    logo_height = 0.8*inch

    logo_path = os.path.join(settings.MEDIA_ROOT, 'MPIDC_Logo.jpg')
    logo_cell = ""
    if os.path.exists(logo_path):
        logo_cell = Image(logo_path, width=2.0*inch, height=logo_height)

    text_block = [
        Paragraph("<b>MP Industrial Development Corporation Ltd.</b>", right_style),
        Paragraph("21, Arera Hills, Bhopal, 462011", right_style),
        Paragraph(f"DIPIP{agenda_data.id}", right_style),
        Spacer(1, max(0, logo_height-32)),  
    ]

    table_data = [[logo_cell, text_block]]
    header_table = Table(
        table_data,
        colWidths=[1.8*inch, 4.7*inch]
    )
    story.append(header_table)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Incentive Agenda", custom_styles['CustomTitle']))
    story.append(Spacer(1, 0.02 * inch))

    story.append(HRFlowable(
        width="100%",
        thickness=1,
        lineCap='round',
        color=colors.HexColor("#1669ae"),
        spaceBefore=0,    
        spaceAfter=0.1*inch  
    ))

    subject = (
        f"<b>Subject: For Determination of Eligibility of Investment Promotion Assistance (IPA) under </b>"
        f"<b>Madhya Pradesh Nivesh Protsahan Yojna-2025 of M/s {safe_str(agenda_data.unit_name)} </b>"
        f"<b>({safe_str(agenda_data.unit_type)}).</b>"
    )
    story.append(Paragraph(subject, styles["Normal"]))
    story.append(Spacer(1, 0.15 * inch))

    details_data = [
        ["1", "Constitution Type", safe_str(agenda_data.constitution_type_name)],
        ["2", "Unit Name", safe_str(agenda_data.unit_name)],
        ["3", "GSTIN and Date", safe_str(agenda_data.gstin_and_date)],
        ["4", "IEM A Number", safe_str(agenda_data.iem_a_number)],
        ["5", "IEM A Date", safe_str(agenda_data.iem_a_date)],
        ["6", "IEM B Number", safe_str(agenda_data.iem_b_number)],
        ["7", "IEM B Date", safe_str(agenda_data.iem_b_date)],
    ]

    location_data = []
    if agenda_data.land_type == "DIPIP (MPIDC)" and agenda_data.plot_type == "Developed":
        location_data = [
            ["8", "Type of Land", safe_str(agenda_data.land_type)],
            ["9", "Plot Type", safe_str(agenda_data.plot_type)],
            ["10", "District", safe_str(agenda_data.district_name)],
            ["11", "Regional Office", safe_str(agenda_data.regional_office_name)],
            ["12", "DIPIP (MPIDC) Industrial Areas", safe_str(agenda_data.industrial_area_name)],
            ["13", "Block", safe_str(agenda_data.block_name)],
            ["14", "Block Category", safe_str(agenda_data.category_of_block)],
            ["15", "Khasra Number", safe_str(agenda_data.industrial_plot)],
            ["16", "Full Address of the Unit", safe_str(agenda_data.address_of_unit)]
        ]
    elif agenda_data.land_type == "DIPIP (MPIDC)" and agenda_data.plot_type == "UnDeveloped":
        location_data = [
            ["8", "Type of Land", safe_str(agenda_data.land_type)],
            ["9", "Plot Type", safe_str(agenda_data.plot_type)],
            ["10", "District", safe_str(agenda_data.district_name)],
            ["11", "Regional Office", safe_str(agenda_data.regional_office_name)],
            ["12", "Block", safe_str(agenda_data.block_name)],
            ["13", "Full Address of the Unit", safe_str(agenda_data.address_of_unit)],
            ["14", "Block Category", safe_str(agenda_data.category_of_block)]
        ]
    elif agenda_data.land_type == "MSME":
        location_data = [
            ["8", "Type of Land", safe_str(agenda_data.land_type)],
            ["9", "District", safe_str(agenda_data.district_name)],
            ["10", "Regional Office", safe_str(agenda_data.regional_office_name)],
            ["11", "MSME Industrial Areas", safe_str(agenda_data.industrial_area_name)],
            ["12", "Block", safe_str(agenda_data.block_name)],
            ["13", "Block Category", safe_str(agenda_data.category_of_block)],
            ["14", "Khasra Number", safe_str(agenda_data.industrial_plot)],
            ["15", "Full Address of the Unit", safe_str(agenda_data.address_of_unit)]
        ]
    elif agenda_data.land_type == "Private land":
        location_data = [
            ["8", "Type of Land", safe_str(agenda_data.land_type)],
            ["9", "District", safe_str(agenda_data.district_name)],
            ["10", "Regional Office", safe_str(agenda_data.regional_office_name)],
            ["11", "Block", safe_str(agenda_data.block_name)],
            ["12", "Block Category", safe_str(agenda_data.category_of_block)],
            ["13", "Khasra Number", safe_str(agenda_data.industrial_plot)],
            ["14", "Full Address of the Unit", safe_str(agenda_data.address_of_unit)]
        ]

    combined_data = details_data + location_data
    details_table = Table(combined_data, colWidths=[30, 180, 270])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (1, -1), 'Helvetica-Bold'),  
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),       
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (1, -1), colors.Color(0.93, 0.93, 0.93)),  
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(details_table)
    story.append(Spacer(1, 0.15 * inch))

    project_details_data = [
        ["1", "Activity Name", safe_str(agenda_data.activity_name)],
        ["2", "Sector", safe_str(agenda_data.sector_name)],
        ["3", "Application Filling Date", format_date(agenda_data.application_filling_date)],
        ["4", "First Production Year", safe_str(agenda_data.first_production_year)],
        ["5", "Commercial Operation Date", format_date(agenda_data.comm_production_date)],
        ["6", "Type of Unit", safe_str(agenda_data.unit_type)],
        ["7", "HT Contract Demand", safe_str(agenda_data.ht_contract_demand)],
        ["8", "Sanctioned Power Load (KVA)", safe_str(agenda_data.saction_power_load)],
        [
            Paragraph("9", field_style),
            Paragraph("Plant & Machinery Investment (in lakhs)", field_style),
            Paragraph(safe_str(agenda_data.investment_in_plant_machinery), value_style)
        ],

        ["10", "Industrial Promotion Policy Scheme", safe_str(agenda_data.ipp)],
        ["11", "Turnover as on COD (in lakhs)", safe_str(existing_agenda_incentive.turnover if existing_agenda_incentive else None)],
        [
            Paragraph("12", field_style),
            Paragraph("Whether the unit is an exporting unit?", field_style),
            Paragraph(
                "Yes" if existing_agenda_incentive and existing_agenda_incentive.is_export_unit else "No",
                value_style
            )
        ],

        ["13", "Is CCIP applicable?", "Yes" if existing_agenda_incentive and existing_agenda_incentive.is_ccip else "No"],
        ["14", "Foreign Direct Investment", "Yes" if existing_agenda_incentive and existing_agenda_incentive.is_fdi else "No"],
    ]
    if existing_agenda_incentive and existing_agenda_incentive.is_fdi:
        project_details_data.extend([
            ["15", "Promoter’s equity (in Lakh)", safe_str(existing_agenda_incentive.promoters_equity_amount)],
            ["16", "Term loan (in Lakh)", safe_str(existing_agenda_incentive.term_loan_amount)],
            ["17", "Foreign Direct Investment (FDI) (in Lakh)", safe_str(existing_agenda_incentive.fdi_amount)],
            ["18", "Total (in Lakh)", safe_str(existing_agenda_incentive.total_finance_amount)],
            ["19", "FDI Percentage", safe_str(existing_agenda_incentive.fdi_percentage)],
        ])
    else:
        project_details_data.extend([
            ["15", "Promoter’s equity (in Lakh)", safe_str(existing_agenda_incentive.promoters_equity_amount)],
            ["16", "Term loan (in Lakh)", safe_str(existing_agenda_incentive.term_loan_amount)],
            ["17", "Total (in Lakh)", safe_str(existing_agenda_incentive.total_finance_amount)],
        ])
    project_table = Table(project_details_data, colWidths=[30, 180, 270])
    project_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (1, -1), 'Helvetica-Bold'),  
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),       
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (1, -1), colors.Color(0.93, 0.93, 0.93)),  
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(project_table)
    story.append(Spacer(1, 0.15 * inch))

    product_table_data = [
        ["S.No.", "Production Date", "Product Name", "Annual Capacity", "Measurement Unit"]
    ] + [
        [
            str(idx + 1),
            safe_str(p.get("comm_production_date")),
            safe_str(p.get("product_name")),
            safe_str(p.get("total_annual_capacity")),
            safe_str(p.get("measurement_unit_name"))
        ]
        for idx, p in enumerate(products_data)
    ]
    product_table = Table(product_table_data, colWidths=[30, 120, 120, 120, 120])
    product_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),               
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.93, 0.93, 0.93)), 
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),                  
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(product_table)
    story.append(Spacer(1, 0.15 * inch))

    emp_table_data = [
        [
            Paragraph("1", field_style),
            Paragraph("Permanent resident of MP", field_style),
            Paragraph(safe_str(agenda_data.employee_of_mp), value_style)
        ],
        [
            Paragraph("2", field_style),
            Paragraph("Out of MP", field_style),
            Paragraph(safe_str(agenda_data.employee_outside_mp), value_style)
        ],
        [
            Paragraph("3", field_style),
            Paragraph("Total", field_style),
            Paragraph(safe_str(agenda_data.total_employee), value_style)
        ],
        [
            Paragraph("4", field_style),
            Paragraph("Total Percentage of Employees permanent resident of MP", field_style),
            Paragraph(f"{safe_str(agenda_data.percentage_in_employee)}%", value_style)
        ],
    ]

    emp_table = Table(emp_table_data, colWidths=[30, 180, 270])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, -1), colors.Color(0.93, 0.93, 0.93)),
        ('FONTNAME', (0, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (2, -1), 'LEFT'),  
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 0.15 * inch))

    recommendation_table = [
        ["1", "Facts about the case", Paragraph(safe_str_value(agenda_data.fact_about_case), custom_styles['CustomHindi'])],
        ["2", "Recommendation of MPIDC", Paragraph(safe_str_value(agenda_data.recommendation), custom_styles['CustomHindi'])],
        ["3", "Proposal to be considered by SLEC", Paragraph(safe_str_value(agenda_data.slec_proposal), custom_styles['CustomHindi'])],
    ]
    rec_table = Table(recommendation_table, colWidths=[0.7 * inch, 2.5 * inch, 3.8 * inch])
    rec_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (1, -1), 'Helvetica-Bold'),  
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),       
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (1, -1), colors.Color(0.93, 0.93, 0.93)),  
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 0.25 * inch))

    footer_right_style = ParagraphStyle(
        name="FooterRight",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontSize=10
    )

    footer_text = Paragraph(
        "<b>Managing Director<br/>MP Industrial Development Corporation Ltd.</b>",
        footer_right_style
    )

    footer_table = Table(
        [["", footer_text]],
        colWidths=[3*inch, 3*inch]
    )
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))

    story.append(Spacer(1, 0.5 * inch))
    story.append(footer_table)

    pdf_directory = os.path.join(settings.MEDIA_ROOT, "agenda_pdfs")
    os.makedirs(pdf_directory, exist_ok=True)
    file_name = f"agenda_{agenda_data.id}.pdf"
    file_path = os.path.join(pdf_directory, file_name)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
        title="Agenda"
    )
    doc.build(story)

    buffer.seek(0)
    with open(file_path, "wb") as f:
        f.write(buffer.read())
    with open(file_path, "rb") as file_to_upload:
        doc_file = SimpleUploadedFile(
            name=file_name,
            content=file_to_upload.read(),
            content_type="application/pdf"
        )
    documents = [{
        "file": doc_file,
        "file_name": doc_file.name,
        "file_type": doc_file.content_type
    }]
    document_folder = user_profile.document_folder if user_profile.document_folder else user_profile.user_id
    url = settings.MINIO_API_HOST + "/minio/uploads"
    upload_response = upload_files_to_minio(documents, url, document_folder)
    if not upload_response["success"]:
        return Response({
            "status": False,
            "message": "File upload failed",
            "error": upload_response["error"],
            "server_response": upload_response["response"]
        }, status=500)
    agenda = IncentiveAgenda.objects.filter(caf_id=agenda_data.caf_id).order_by('-id').first()
    if agenda:
        agenda.agenda_file = upload_response["data"][0]["path"]
        agenda.save()
        created = False
    else:
        agenda = IncentiveAgenda.objects.create(
            caf_id=agenda_data.caf_id,
            agenda_file=upload_response["data"]["path"]
        )
        created = True
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        return Response({
            "status": False,
            "message": "File removal failed"
        }, status=500)
    return upload_response["data"][0]["path"]

import time
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE_PATH = os.path.join(BASE_DIR, "incentive", "agenda_logs.txt")

import os

def log_api_timing(caf_id,current_status, status, start_time,file_path=LOG_FILE_PATH ):
    try:

        end_time = time.time()
        duration = (end_time - start_time)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(file_path, "a", encoding="utf-8") as file:
            file.write(f"CAFid :{caf_id} | [{timestamp}] |Current status:{current_status}| API status: {status} | Duration: {duration}s\n")
    except Exception as e:
        print(f"Logging Error: {e}")
        pass


def count_page(base64_file):
    try:
        pdf_bytes = base64.b64decode(base64_file)
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        total_pages = len(pdf_reader.pages)
        return(total_pages)
    
    except Exception as e:
        pass
