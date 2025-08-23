from django.utils import timezone
from django.db import models
from authentication.models import *


# Create your models here.

class Designation(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "caf_designation"

class IndustryType(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_industry_type"


STATUS_CHOICES = [
    (0, "Inactive"),
    (1, "Active"),
]

class Activity(models.Model):
    name = models.CharField(max_length=255)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_activity"

class Sector(models.Model):
    name = models.TextField()
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="sectors"
    )
    display_order = models.IntegerField(default=9999)
    icon_name = models.CharField(max_length=255, null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    nic_code = models.CharField(max_length=20, null=True)
    show_in_kya = models.BooleanField(default=False)
    show_in_incentive_calc = models.BooleanField(default=False)
    incentive_method = models.CharField(max_length=100, default="get_general_incentive")
    sector_multiple = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    incentive_name = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "sws_sector"

class SubSector(models.Model):
    name = models.TextField()
    sector = models.ForeignKey(
        Sector, on_delete=models.CASCADE, related_name="sector"
    )
    nic_code = models.CharField(max_length=20, null=True)
    show_in_kya = models.BooleanField(default=False)
    display_order = models.IntegerField(default=9999)
    class Meta:
        db_table='sws_subsector'

class State(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "sws_state"


class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "sws_district"


class RegionalOffice(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "sws_regional_office"


class IndustrialAreaList(models.Model):
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="industrial_areas"
    )
    name = models.CharField(max_length=255)
    authority = models.CharField(max_length=30, default="")
    incentive_authority = models.CharField(max_length=30, default="", null=True, blank=True)
    develop_status=models.CharField(max_length=30, default="Developed")
    water = models.BooleanField(default=False)
    road = models.BooleanField(default=False)
    electricity = models.BooleanField(default=False)
    nearest_city = models.CharField(max_length=150, null=True, blank=True)
    nearest_railway = models.CharField(max_length=150, null=True, blank=True)
    nearest_airport = models.CharField(max_length=150, null=True, blank=True)
    nearest_road = models.CharField(max_length=150, null=True, blank=True)
    nearest_port = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "sws_industrial_area"


class CustomerIntentionProject(models.Model):
    STATUS_CHOICES=[
        ("regular","Regular"),
        ("incentive","Incentive")
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    activities = models.ForeignKey(Activity, on_delete=models.CASCADE, null=True, blank=True)  
    activity = models.CharField(max_length=100, null=True, blank=True)
    sectors = models.ForeignKey(Sector, on_delete=models.CASCADE, null=True, blank=True) 
    sector = models.CharField(max_length=255, null=True, blank=True)
    product_name = models.TextField(null=True, blank=True)
    product_proposed_date = models.CharField(max_length=50, null=True, blank=True)
    project_description = models.TextField(null=True, blank=True)
    total_investment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    power_required = models.CharField(max_length=50, null=True, blank=True)
    water_required = models.CharField(max_length=50, null=True, blank=True)
    employment = models.CharField(max_length=50, null=True, blank=True)
    intention_id = models.CharField(max_length=50, default="")
    status = models.CharField(max_length=20, default="new")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    investment_type = models.CharField(max_length=100, null=True, blank=True)
    subsectors = models.ForeignKey(SubSector, on_delete=models.CASCADE, null=True, blank=True) 
    sub_sector = models.TextField(null=True, blank=True)
    investment_in_pm = models.CharField(max_length=100, null=True, blank=True)
    total_land_required = models.CharField(max_length=100, null=True, blank=True)
    land_identified = models.CharField(max_length=5, null=True, blank=True)
    land_type = models.CharField(max_length=100, null=True, blank=True)
    land_ia = models.ForeignKey(IndustrialAreaList, on_delete=models.CASCADE, null=True, blank=True)
    land_industrial_area = models.CharField(max_length=200, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    districts = models.ForeignKey(District, on_delete=models.CASCADE, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pincode = models.IntegerField(null=True, blank=True)
    preffered_district = models.CharField(max_length=255, null=True, blank=True)
    intention_type=models.CharField(max_length=10, choices=STATUS_CHOICES, default="regular")
    intention_file_path=models.TextField(null=True, blank=True)
 
    class Meta:
        db_table = "caf_project_information"

class CAF(models.Model):
    intention = models.ForeignKey(
        CustomerIntentionProject, on_delete=models.CASCADE, null=True
    )
    name = models.CharField(max_length=255)  # Unit Name
    firm_registration_number = models.CharField(
        max_length=255
    )  # Firm Registration Number
    scale_of_industry = models.CharField(
        max_length=255, blank=True, null=True
    )  # Scale of Industry (can be optional)
    firm_pan_number = models.CharField(max_length=10)  # Firm PAN Number
    firm_gstin_number = models.CharField(max_length=15)  # Firm GSTIN Number
    status = models.CharField(max_length=30, null=False, default="Not Started")

    class Meta:
        db_table = "caf_detail"


class CommonApplication(models.Model):
    CONTACT_TYPES = (
        ("Director", "Director"),
        ("Manager", "Manager"),
        ("Partner", "Partner"),
        ("Proprietor", "Proprietor"),
        ("Authorized", "Authorized"),
    )

    name = models.CharField(max_length=255)
    desig = models.ForeignKey(
        Designation, on_delete=models.CASCADE, null=True, blank=True
    )
    designation = models.CharField(max_length=255)
    #due to circular storing the country code in integer
    country_code = models.IntegerField(null=True, blank=True)
    country_code_value = models.CharField(max_length=15, null=True, blank=True)
    mobile_number = models.CharField(max_length=15)
    email_id = models.EmailField()
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    caf = models.ForeignKey(
        CAF, on_delete=models.CASCADE, related_name="caf_contact_detail"
    )
    other_designation = models.CharField(max_length=50, null=True, blank=True,help_text= "Other designation")

    class Meta:
        db_table = "caf_contact_detail"


class Address(models.Model):
    ADDRESS_TYPES = (
        ("Registered", "Registered Office"),
        ("Communication", "Communication"),
    )

    caf = models.ForeignKey(CAF, on_delete=models.CASCADE, related_name="caf_address")
    address_line = models.CharField(max_length=255)
    districts = models.ForeignKey(
        District, on_delete=models.CASCADE, null=True, blank=True
    )
    district = models.CharField(max_length=255)
    states = models.ForeignKey(
        State, on_delete=models.CASCADE, null=True, blank=True
    )
    state = models.CharField(max_length=255)
    pin_code = models.CharField(max_length=6)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES)

    class Meta:
        db_table = "caf_addess"


class Tehsil(models.Model):
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="tehsils"
    )
    name = models.CharField(max_length=255)

    class Mets:
        db_table = "sws_tehsil"


class SectorProductDetails(models.Model):
    name = models.CharField(max_length=255)
    sector = models.ForeignKey(
        Sector, on_delete=models.CASCADE, related_name="products"
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_sector_product_details"


class PollutionType(models.Model):
    name = models.CharField(max_length=255)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_pollution_type"


class DepartmentList(models.Model):
    name = models.CharField(max_length=255, null=False, default="")
    status = models.BooleanField(
        default=True, verbose_name="0 for inactive & 1 for active"
    )
    code = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_department"


class CAFInvestmentDetails(models.Model):
    caf = models.ForeignKey(
        CAF, on_delete=models.CASCADE, related_name="caf_investment_details"
    )
    type_of_investment = models.CharField(max_length=50, default="")
    project_name = models.CharField(max_length=255, default="")
    activity = models.CharField(max_length=20, default="")
    activities = models.ForeignKey(Activity, on_delete=models.CASCADE, null=True, blank=True)  
    sectors = models.ForeignKey(Sector, on_delete=models.CASCADE, null=True, blank=True) 
    sector = models.CharField(max_length=255, default="")
    sub_sector = models.TextField(null=True, blank=True)
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE, null=True, blank=True)
    product_name = models.TextField(default="")
    do_you_have_land = models.BooleanField(default=False)
    type_of_land = models.CharField(max_length=100, default="", null=True, blank=True)
    industrial_area = models.CharField(max_length=255, default="", null=True, blank=True)
    land_ia = models.ForeignKey(IndustrialAreaList, on_delete=models.CASCADE, null=True, blank=True)
    land_district = models.CharField(max_length=100, default="", null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, null=True, blank=True)
    preffered_districts = models.CharField(max_length=200, default="", null=True, blank=True)
    land_address = models.CharField(max_length=255, default="", null=True, blank=True)
    land_pincode = models.CharField(max_length=6, default="", null=True, blank=True)
    land_registry_number = models.CharField(max_length=100, default="", null=True, blank=True)
    total_land_area = models.IntegerField()
    total_investment = models.CharField(max_length=20, default="")
    plant_machinary_value = models.CharField(max_length=100, default="")
    product_proposed_date = models.CharField(max_length=50, default="NA")
    water_limit = models.CharField(max_length=20, default="")
    power_limit = models.CharField(max_length=20, default="")
    total_employee = models.IntegerField(default=0)
    total_local_employee = models.IntegerField(default=0)
    export_oriented_unit = models.BooleanField(default=False)
    export_percentage = models.CharField(max_length=20, default="", null=True, blank=True)
    acknowledge = models.BooleanField(default=False)
    acknowledge_time = models.CharField(max_length=40, default="",null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "caf_investment_details"

class IntentionIdGenerator(models.Model):
    investment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    investment_id = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sws_intentions_generator"


class PlotDetails(models.Model):
    plot = models.CharField(max_length=255, default="")
    regional_office = models.CharField(max_length=255,default="")
    ro = models.ForeignKey(
        RegionalOffice, on_delete=models.CASCADE, related_name="plot_regional_offices",null=True
    )
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    ia = models.ForeignKey(
        IndustrialAreaList, on_delete=models.CASCADE, related_name="industrial_areas",null=True
    )
    industrial_area = models.CharField(max_length=100,default="")
    industrial_area_type = models.CharField(max_length=100,default="")
    total_land_area = models.IntegerField(default=0)
    total_no_of_plots = models.IntegerField(default=0)
    total_plot_area = models.IntegerField(default=0)
    booked_plot_no = models.IntegerField(default=0)
    booked_plots_area = models.IntegerField(default=0)
    alloted_plot_no = models.IntegerField(default=0)
    alloted_area = models.IntegerField(default=0)
    vacant_plots = models.IntegerField(default=0)
    vacant_plots_area = models.IntegerField(default=0)
    not_for_sale_plots = models.IntegerField(default=0)
    not_for_plots_area = models.IntegerField(default=0)
    latitude = models.CharField(max_length=20,default="")
    longitude = models.CharField(max_length=20,default="")
    status = models.CharField(max_length=20,default="")
    extra_feature = models.TextField(default="")

    class Meta:
        db_table = "sws_plot_details"


class CustomerIntentionPDF(models.Model):
    customer_project = models.OneToOneField(
        CustomerIntentionProject, on_delete=models.CASCADE, related_name="pdf_document"
    )
    intention_id = models.CharField(max_length=50, unique=True)
    intention_doc = models.FileField(upload_to="intention_pdfs/", blank=True, null=True)
    doc_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "sws_customer_intention_pdf"


class CAFCreationPDF(models.Model):
    caf = models.OneToOneField(CAF, on_delete=models.CASCADE, related_name="caf_generated_pdfs")
    caf_reference_id  = models.CharField(max_length=100, unique=True)
    caf_doc = models.TextField(null=True, blank=True)
    pdf_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_document_sign = models.BooleanField(default=False)

    class Meta:
        db_table = "sws_caf_pdf"

class KnowYourPolicy(models.Model):
    title = models.CharField(max_length=255, default="")
    subtitle = models.TextField(null=True, blank= True)
    policy_type = models.SmallIntegerField(default=2,help_text="1 for sector policy & 2 for other policies")
    policy_img = models.CharField(max_length=255, default="", null=False, blank=True)
    content = models.TextField(default="")
    sector = models.ForeignKey(
        Sector, on_delete=models.SET_NULL, null=True, blank=True
    )
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "In-Active"),
        ("deleted", "Deleted")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        db_table='sws_policies'

class RegionalOfficeDistrictMapping(models.Model):
    regional_office = models.ForeignKey(
        RegionalOffice, on_delete=models.CASCADE, related_name="rof_regional_offices"
    )
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="rof_district"
    )
    display_order = models.IntegerField(default=9999)
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "In-Active"),
        ("deleted", "Deleted")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        db_table = "sws_ro_district_mappings"


class KnowYourPolicyDocument(models.Model):
    kyp = models.ForeignKey(
        KnowYourPolicy, on_delete=models.CASCADE, related_name="kyp_policy"
    )
    document_name = models.CharField(max_length=255, null=True, blank=True)
    document_link = models.TextField(default="")
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "In-Active"),
        ("deleted", "Deleted")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        db_table='sws_policy_documents'

class DistrictBlockList(models.Model):
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="district_blocks"
    )
    name = models.CharField(max_length=255)
    block_priority = models.CharField(max_length=20, default="Non Priority", help_text="Priority or Non Priority")

    class Meta:
        db_table = "sws_district_blocks"

class MeasurementUnitList(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, default="active",help_text="active, inactive or deleted")

    class Meta:
        db_table = "sws_measurements_units"

class CustomerHelpdesk(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=100)
    mobile_no = models.CharField(max_length=13)
    message = models.TextField()
    acknowledgement = models.BooleanField(default=False)
    status = models.CharField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "sws_customer_helpdesk"

class CustomerSubscriptions(models.Model):
    email = models.EmailField(max_length=100)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_customer_subscriptions"


class FeedbackFormModel(models.Model):
    first_name= models.CharField(max_length=255,blank=True,null=True,default=None)
    last_name= models.CharField(max_length=255,blank=True,null=True,default=None)
    mobile_no = models.CharField(max_length=13,blank=True , null= True, default=None)
    email = models.EmailField(max_length=255,blank=True,null=True,default=None)
    address = models.TextField(blank=True,null=True,default="")
    state = models.ForeignKey(State, on_delete=models.CASCADE,blank=True,null=True)
    state_name = models.CharField(max_length=255,blank=True,null=True,default=None)
    district = models.ForeignKey(District, on_delete=models.CASCADE,blank=True,null=True)
    district_name = models.CharField(max_length=255,blank=True,null=True,default=None)
    organization = models.CharField(max_length=255,blank=True,null=True,default=None)
    designation= models.CharField(max_length=255,blank=True,null=True,default=None)
    request_type = models.CharField(max_length=255,blank=True,null=True,default=None)
    subject = models.CharField(max_length=255,blank=True,null=True,default=None)
    details = models.TextField(blank=True,null=True)
    document_link = models.TextField(default="",blank=True,null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_feedback_form"


class ServiceConfigModel(models.Model):
    approval = models.ForeignKey("approval.ApprovalList", on_delete=models.CASCADE, related_name="approval_service_config")
    deparment = models.ForeignKey(DepartmentList, on_delete=models.CASCADE, related_name="deparment_service_config")
    service_charge = models.DecimalField(max_digits=12, decimal_places=3, default=0.0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_service_config"

class ServiceDynamicFieldModel(models.Model):
    sevice = models.ForeignKey(ServiceConfigModel, on_delete=models.CASCADE, related_name="approval_service_charge", blank=True, null=True)
    field_tag = models.CharField(max_length=255,blank=True,null=True)
    field_title = models.TextField(blank=True,null=True)
    field_type = models.CharField(max_length=20, blank=True,null=True)
    field_value = models.JSONField(blank=True,null=True)
    field_status = models.BooleanField(default=True)
    field_order = models.IntegerField(default=999)

    class Meta:
        db_table = "sws_service_dynamic_fields"

class ServiceDepartmentAPIModel(models.Model):
    deparment = models.ForeignKey(DepartmentList, on_delete=models.CASCADE, related_name="deparment_api")
    client_key = models.CharField(max_length=255,blank=True,null=True)
    client_secret = models.CharField(max_length=255,blank=True,null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_service_api"

class ServiceDepartmentAPILogModel(models.Model):
    deparment = models.ForeignKey("approval.UserCAFService", on_delete=models.CASCADE, related_name="deparment_api_log")
    message = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_service_api_logs"


class ServiceRequestNumberModel(models.Model):
    caf = models.ForeignKey(
        CAF, on_delete=models.CASCADE, null=True, blank=True
    )
    service_request_number = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sws_service_request_number"