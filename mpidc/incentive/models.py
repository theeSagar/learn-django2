from django.db import models
from authentication.models import Country, Role, User
from sws.models import (
    Activity,
    CustomerIntentionProject,
    District,
    DistrictBlockList,
    IndustrialAreaList,
    MeasurementUnitList,
    RegionalOffice,
    Sector,
    SubSector,
)
from userprofile.models import OrganizationType

class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class IncentiveCAF(TimeStampModel):
    intention = models.ForeignKey(
        CustomerIntentionProject, on_delete=models.CASCADE, related_name="incentive_intention_id"
    )
    status = models.CharField(max_length=100, default="In-Progress", help_text="In-Progress, Completed, Deleted")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="caf_user")
    caf_pdf_url = models.CharField(max_length=150, default="", null=True, blank=True, help_text="URL of PDF")
    incentive_caf_number = models.CharField(max_length=30, default="", null=True, blank=True, help_text="caf number")
    acknowledgement = models.BooleanField(default=False)
    acknowledgement_date = models.DateTimeField(null=True, blank=True)
    is_offline = models.BooleanField(default=False)
    sla_days = models.PositiveIntegerField(null=True, blank=True)
    sla_due_date = models.DateField(null=True, blank=True)
    current_approver_role = models.ForeignKey(
        Role, on_delete=models.CASCADE, null=True, blank=True, related_name="caf_current_role"
    )
    is_document_sign = models.BooleanField(default=False)
    is_instruction_acknowledgement = models.BooleanField(default=False)

    class Meta:
        db_table = "incentive_caf_details"

#In denotes for Incentive
class InCAFProject(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="caf_project"
    )
    unit_name = models.CharField(max_length=255, null=True, blank=True, help_text="Company Name")
    constitution_type_name = models.CharField(max_length=100, null=True, blank=True, help_text="Constitution Type Name")
    constitution_type = models.ForeignKey(
        OrganizationType, on_delete=models.CASCADE, null=True, blank=True, related_name="org_type_id"
    )
    intention_id =  models.CharField(max_length=50, null=True, blank=True, help_text="Intention Id")
    date_of_intention = models.DateField(null=True, blank=True, help_text="Date of filled Intention")
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, null=True, blank=True, related_name="in_district"
    )
    district_name = models.CharField(max_length=50, null=True, blank=True, help_text="District names")
    regional_office = models.ForeignKey(
        RegionalOffice, on_delete=models.CASCADE, null=True, blank=True, related_name="in_regional"
    )
    regional_office_name = models.CharField(max_length=50, null=True, blank=True, help_text="District names")
    block = models.ForeignKey(
        DistrictBlockList, on_delete=models.CASCADE, null=True, blank=True, related_name="block_district"
    )
    block_name = models.CharField(max_length=75, null=True, blank=True, help_text="Block names")
    land_type = models.CharField(max_length=75, null=True, blank=True, help_text="Land Type")
    industrial_area = models.ForeignKey(
        IndustrialAreaList, on_delete=models.SET_NULL, blank=True, null=True, related_name="in_industrial_area"
    )
    industrial_area_name = models.CharField(max_length=255, null=True, blank=True, help_text="industrial area name")
    industrial_plot = models.CharField(max_length=200, null=True, blank=True, help_text="industrial plot")
    address_of_unit = models.TextField(null=True, blank=True, help_text="Address of Unit")
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, null=True, blank=True, related_name="in_activity"
    )
    activity_name = models.CharField(max_length=50, null=True, blank=True, help_text="activity name")
    sector = models.ForeignKey(
        Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="in_sector"
    )
    sector_name = models.TextField(null=True, blank=True, help_text="Sector name")
    sub_sector = models.ForeignKey(
        SubSector, on_delete=models.CASCADE, null=True, blank=True, related_name="in_sub_sector"
    )
    sub_sector_name = models.CharField(max_length=250, null=True, blank=True, help_text="Sub Sector name")
    contact_person_name = models.CharField(max_length=200, null=True, blank=True, help_text="Name of authorised person")
    contact_email = models.EmailField(max_length=100, null=True, blank=True, help_text="Email of authorised person")
    country_code = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE, related_name="auth_country_code")
    country_code_name = models.CharField(max_length=15, null=True, blank=True, help_text="Code value")
    contact_mobile_no = models.CharField(max_length=16, null=True, blank=True, help_text="Mobile number of authorised person")
    md_person_name = models.CharField(max_length=200, null=True, blank=True, help_text="Name of md person")
    md_contact_email = models.EmailField(max_length=100, null=True, blank=True, help_text="Email of md person")
    md_country_code = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE,  related_name="md_country_code")
    md_country_code_name = models.CharField(max_length=15, null=True, blank=True, help_text="Code value")
    md_contact_mobile_no = models.CharField(max_length=16, null=True, blank=True, help_text="Mobile number of md person")
    contact_landline_no = models.CharField(max_length=16, default="", null=True, blank=True, help_text="Landline Number")
    company_address = models.TextField(null=True, blank=True, help_text="Address of company")
    company_address_pincode = models.CharField(max_length=6, null=True, blank=True, help_text="Pincode of company")
    iem_a_number = models.CharField(max_length=100, default="", null=True, blank=True, help_text="IEM Part A Number")
    iem_a_date = models.DateField(null=True, blank=True, help_text="IEM Part A Date")
    iem_b_number = models.CharField(max_length=100, default="", null=True, blank=True, help_text="IEM Part B Number")
    iem_b_date = models.DateField(null=True, blank=True, help_text="IEM Part B Date")
    gstin = models.CharField(max_length=15, default="", null=True, blank=True, help_text="GST number")
    gstin_issue_date = models.DateField(null=True, blank=True, help_text="GST issue date")
    unit_type = models.CharField(max_length=60, default="", null=True, blank=True, help_text="unit_type")
    is_ccip = models.BooleanField(default= False)
    dipip_type = models.CharField(max_length=255,null=True,blank=True, help_text="DIPIP type of land")
    plot_type = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=50, null=True, blank=True)
    other_designation = models.CharField(max_length=50,null=True,blank=True)
    class Meta:
        db_table = "incentive_caf_project_details"
    
class InCAFInvestment(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_investment"
    )
    comm_production_date = models.DateField(null=True, blank=True, help_text="Commercial Production Date")
    total_investment_land = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    total_investment_other_asset = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    turnover = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    total_investment_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_in_plant_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_in_building = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_fdi = models.BooleanField(default=False)
    fdi_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    csr = models.CharField(max_length=100, null=True, blank=True)
    is_export_unit = models.BooleanField(default=False)
    promoters_equity_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    term_loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fdi_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_finance_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_land_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_in_plant_machinery_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_in_building_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_other_asset_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_investment_amount_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_furniture_fixtures = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    is_csr = models.BooleanField(default= False)
    investment_in_house_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_in_house = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_captive_power_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_captive_power = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_energy_saving_devices_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_energy_saving_devices = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_imported_second_hand_machinery_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_imported_second_hand_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_refurbishment_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_refurbishment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    other_assets_remark = models.CharField(max_length=255, null=True, blank=True, help_text="Other Assets Remarks")

    class Meta:
        db_table = "incentive_caf_investment_details"

class InCAFPower(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_power"
    )
    connection_type = models.CharField(max_length=10, null=True, blank=True, help_text="New or Existing")
    ht_contract_demand = models.CharField(max_length=15, null=True, blank=True, help_text="11KV, 33KV etc")
    date_of_connection = models.DateField(null=True, blank=True, help_text="Date of connection")
    load_consumption = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Load consumption")
    existing_load = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Existing Load consumption")
    additional_load = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Additional Load consumption")
    date_additional_load = models.DateField(null=True, blank=True, help_text="Additional Load Date")
    date_of_connection_before_expansion = models.DateField(null=True, blank=True, help_text="Before expansion")
    connection_type_before_expansion = models.CharField(max_length=10, null=True, blank=True, help_text="Before expansion")
    power_load_before_expansion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank= True, help_text="Load before expansion")
    meter_before_expansion = models.CharField(max_length=255, null=True, blank=True, help_text="Meter details before expansion")
    meter_details = models.CharField(max_length=255,null=True,blank=True,help_text="Meter details")
    enhancement_load_date = models.DateField(null=True, blank=True, help_text="Data of load enhancement")

    class Meta:
        db_table = "incentive_caf_power_details"


class InCAFPowerLoad(models.Model):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_power_load"
    )
    supplementary_load = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank= True, help_text="Supplementary Saction load")
    supplementary_load_date = models.DateField(null=True, blank= True, help_text="Supplementary Saction load date")
    is_supplementary_load = models.BooleanField(default= False)

    class Meta:
        db_table = "incentive_caf_power_load_details"

class InCAFSubMeter(models.Model):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_submeter"
    )
    meter_number = models.CharField(max_length=100, null=True, blank=True, help_text="Sub meter details")
    
    class Meta:
        db_table = "incentive_caf_submeter_details"

class InCAFEmployment(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_employment"
    )
    employees_from_mp = models.IntegerField(null=True, blank=True, help_text="Employees from MP")
    employees_outside_mp = models.IntegerField(null=True, blank=True, help_text="Employees Outside From MP")
    total_employee = models.IntegerField(null=True, blank=True, help_text="Total Employee")
    employee_from_mp_before_expansion = models.IntegerField(null=True, blank=True,help_text="employee before expansion")
    employees_outside_mp_before_expansion = models.IntegerField(null=True, blank=True,help_text="employee under expansion")
    total_employee_before_expansion = models.IntegerField(null=True, blank=True,help_text="total no employee under expansion")
    employee_domicile_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Domicile percentage")
    employee_domicile_percentage_before_expansion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Domicile percentage before expansion")
    number_of_differently_abled_employees = models.IntegerField(null=True,blank=True , help_text = "Number of differently abled employees")
    percentage_of_differently_abled_employees = models.DecimalField(null=True, blank=True , max_digits=5, decimal_places=2, help_text= "Percentange of differently abled employees")
    
    class Meta:
        db_table = "incentive_caf_employement_details"

class InCAFProduct(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_products"
    )
    measurement_unit = models.ForeignKey(
        MeasurementUnitList, on_delete=models.CASCADE, related_name="incaf_measurement", null=True, blank= True
    )
    measurement_unit_name = models.CharField(max_length=255, null=True, blank= True, help_text="Measurement unit names")
    other_measurement_unit_name = models.CharField(max_length=255, null=True, blank= True, help_text="Measurement unit names")
    product_name = models.TextField(null=True, blank=True, help_text="Product Name")
    total_annual_capacity = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="Annual Capacity")
    ime_before_expansion = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="IME Before Capacity")
    avg_production_before_expansion = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="Avg Before Capacity")
    annual_capacity_before_expansion = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="Annual Capacity Before Capacity")
    product_type = models.CharField(default="New",max_length = 50, null=True,blank=True)
    
    class Meta:
        db_table = "incentive_caf_product_details"


class InCAFIncentive(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_incentive"
    )
    is_ipp = models.BooleanField(null=True, blank=True,)
    is_gia = models.BooleanField(null=True, blank=True,)
    is_mandifee = models.BooleanField(null=True, blank=True,)
    comm_proudction_date = models.DateField(null=True, blank=True, help_text="is_ipp true then cpd needed")
    first_purchase_date = models.DateField(null=True, blank=True, help_text="is_ipp true then first purchased needed")
    first_sale_date = models.DateField(null=True, blank=True, help_text="is_ipp true then first sale needed")
    incentive_year = models.CharField(max_length=10, null=True, blank=True, help_text="is_ipp true then first incentive year needed")
    type_of_wms = models.CharField(max_length=75, null=True, blank=True, help_text="is_gia true then wms needed")
    wms_total_expenditure = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="is_gia true then wms expenditure needed")
    mandi_license = models.CharField(max_length=50, null=True, blank=True, help_text="is_mandiifee true then license needed")
    mandi_license_date = models.DateField(null=True, blank=True, help_text="is_mandiifee true then license date needed")
    incentive_json = models.JSONField(null=True, blank=True, help_text="store json data")
    
    class Meta:
        db_table = "incentive_caf_incentive_details"

class DocumentList(TimeStampModel):
    name = models.TextField(null=False, blank=False, help_text="Document Name")
    title = models.TextField(null=True, blank=True, help_text="Title Name")
    template_file_path = models.TextField(null=True, blank=True, help_text="Template file path")
    entity_doc_type = models.CharField(max_length=50, null=True, blank=True, help_text="Document Type")
    digi_doc_type = models.CharField(max_length=50, null=True, blank=True, help_text="Digi doc Type")
    file_type = models.CharField(max_length=100, null=True, blank=True, help_text="Type of document upload" )

    class Meta:
        db_table = "document_list"

class InCAFDocuments(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_documents"
    )
    document_path = models.CharField(max_length=200, null=True, blank=True, help_text="is_ipp true then first incentive year needed")
    document = models.ForeignKey(
        DocumentList, on_delete=models.CASCADE, related_name="incaf_documents"
    )
    document_name = models.CharField(max_length=150, default="", null=False, blank=False, help_text="document name")

    class Meta:
        db_table = "incentive_caf_documents_details"

class IncentiveActivityHistory(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_activity"
    )
    user_name = models.CharField(max_length=200, null=True, blank=True, help_text="approver name")
    user_role = models.CharField(max_length=200, null=True, blank=True, help_text="approver designation")
    ip_address = models.CharField(max_length=30, null=True, blank=True, help_text="ip address")
    activity_status = models.CharField(max_length=100, null=True, blank=True)
    caf_status = models.CharField(max_length=100, null=True, blank=True)
    status_remark = models.CharField(max_length=150, null=True, blank=True)
    activity_result = models.CharField(max_length=30, null=True, blank=True)
    mac_address=models.CharField(max_length=200,null=True,blank=True,help_text="mac address")
    
    class Meta:
        db_table = "incentive_activity_history"

class IncentiveAgenda(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_agenda"
    )
    status = models.CharField(max_length=50, null=False, blank=False, help_text="Pending for creation or created")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="incaf_agenda_user"
    )
    created_user_name = models.CharField(max_length=100, null=True, blank=True, help_text="name of user created the agenda")
    unit_name = models.CharField(max_length=255, null=True, blank=True, help_text="Company Name")
    constitution_type_name = models.CharField(max_length=100, null=True, blank=True, help_text="Constitution Type Name")
    constitution_type = models.ForeignKey(
        OrganizationType, on_delete=models.CASCADE, null=True, blank=True, related_name="agendat_org_type_id"
    )
    gstin_and_date = models.CharField(max_length=255, null=True, blank=True, help_text="GSTIN & Date")
    iem_a_number = models.CharField(max_length=100, null=True, blank=True, help_text="IEM Part A Number")
    iem_a_date = models.DateField(null=True, blank=True, help_text="IEM Part A Date")
    iem_b_number = models.CharField(max_length=100, null=True, blank=True, help_text="IEM Part B Number")
    iem_b_date = models.DateField(null=True, blank=True, help_text="IEM Part B Date")
    block_name = models.CharField(max_length=75, null=True, blank=True, help_text="Block names")
    address_of_unit = models.TextField(null=True, blank=True, help_text="Address of Unit")
    category_of_block = models.CharField(max_length=15, null=True, blank=True, help_text="Priority or Non Priority")
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, null=True, blank=True, related_name="agenda_activity"
    )
    activity_name = models.CharField(max_length=50, null=True, blank=True, help_text="activity name")
    sector = models.ForeignKey(
        Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="agenda_sector"
    )
    sector_name = models.CharField(max_length=200, null=True, blank=True, help_text="Sector name")
    sub_sector = models.ForeignKey(
        SubSector, on_delete=models.CASCADE, null=True, blank=True, related_name="agenda_sub_sector"
    )
    sub_sector_name = models.TextField(null=True, blank=True, help_text="SubSector name")
    application_filling_date = models.DateField(null=True, blank=True, help_text="Application Filling Date")
    first_production_year = models.CharField(max_length=10, null=True, blank=True, help_text="First product year")
    unit_type = models.CharField(max_length=60, null=True, blank=True, help_text="unit_type")
    comm_production_date = models.DateField(null=True, blank=True, help_text="Commercial Production Date")
    ht_contract_demand = models.CharField(max_length=15, default="", null=True, blank=True, help_text="11KV, 33KV etc")
    saction_power_load = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="decimal values")
    investment_in_plant_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligible_investment_plant_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bipa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    yearly_bipa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ipp = models.CharField(max_length=200, null=True, blank=True, help_text="IPP name")
    eligible_period = models.CharField(max_length=200, null=True, blank=True, help_text="Eligible Period of Assitance")
    employee_of_mp = models.IntegerField(null=True, blank=True)
    employee_outside_mp = models.IntegerField(null=True, blank=True)
    total_employee = models.IntegerField(null=True, blank=True)
    percentage_in_employee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fact_about_case = models.TextField(null=True, blank=True)
    recommendation = models.TextField(null=True, blank=True)
    slec_proposal = models.TextField(null=True, blank=True)
    agenda_file = models.TextField(null=True, blank=True)
    is_document_sign = models.BooleanField(default=False)
    employee_of_mp_before_expansion = models.IntegerField(null=True, blank=True)
    employee_outside_mp_before_expansion = models.IntegerField(null=True, blank=True)
    total_employee_before_expansion = models.IntegerField(null=True, blank=True)
    employee_domicile_percentage_before_expansion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Domicile percentage before expansion")
    number_of_differently_abled_employees = models.IntegerField(null=True,blank=True , help_text = "Number of differently abled employees")
    percentage_of_differently_abled_employees = models.DecimalField(null=True, blank=True , max_digits=5, decimal_places=2, help_text= "Percentange of differently abled employees")
    block = models.ForeignKey(
        DistrictBlockList, on_delete=models.CASCADE, null=True, blank=True, related_name="agenda_block_district"
    )
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, null=True, blank=True, related_name="agenda_district"
    )
    district_name = models.CharField(max_length=50, null=True, blank=True, help_text="District names")
    regional_office = models.ForeignKey(
        RegionalOffice, on_delete=models.CASCADE, null=True, blank=True, related_name="agenda_regional"
    )
    regional_office_name = models.CharField(max_length=50, null=True, blank=True, help_text="District names")
    land_type = models.CharField(max_length=75, null=True, blank=True, help_text="Land Type")
    industrial_area = models.ForeignKey(
        IndustrialAreaList, on_delete=models.SET_NULL, blank=True, null=True, related_name="agenda_industrial_area"
    )
    industrial_area_name = models.CharField(max_length=255, null=True, blank=True, help_text="industrial area name")
    industrial_plot = models.CharField(max_length=200, null=True, blank=True, help_text="industrial plot")
    plot_type = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = "incentive_agenda"

class IncentiveAgendaProduct(models.Model):
    agenda = models.ForeignKey(
        IncentiveAgenda, on_delete=models.CASCADE,  null=True, related_name="agenda_product"
    )
    measurement_unit = models.ForeignKey(
        MeasurementUnitList, on_delete=models.CASCADE, related_name="agenda_measurement", null=True, blank= True
    )
    measurement_unit_name = models.CharField(max_length=255, null=True, blank= True, help_text="Measurement unit names")
    product_name = models.TextField(null=True, blank= True, help_text="Product Name")
    total_annual_capacity = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="Annual Capacity")
    comm_production_date = models.DateField(null=True, blank= True, help_text="Commercial Production Date")

    class Meta:
        db_table = "incentive_agenda_products"


class IncentiveAuditLog(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_audit"
    )
    module = models.CharField(max_length=100, null=True, blank=True, help_text="module_name")
    user_name = models.CharField(max_length=200, null=True, blank=True, help_text="user name")
    user_role = models.CharField(max_length=200, null=True, blank=True, help_text="user role")
    action_type = models.CharField(max_length=200, null=True, blank=True, help_text="form field")
    old_value = models.CharField(null=True, blank=True, help_text="old_value")
    new_value = models.CharField(null=True, blank=True, help_text="new_value")
    mac_address=models.CharField(max_length=200,null=True,blank=True,help_text="mac address")    
    
    class Meta:
        db_table = "incentive_audit_logs"


class IncentiveApprovalHistory(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_approval"
    )
    incentive_action = models.CharField(max_length=100, null=True, blank=True, help_text="forward or raise query")
    next_approver_designation = models.CharField(max_length=200, null=True, blank=True, help_text="GM, CGM etc")
    approving_document = models.CharField(max_length=200, null=True, blank=True, help_text="document uploaded")
    approving_remark = models.TextField(null=True, blank=True)
    name_of_authority = models.CharField(max_length=200, null=True, blank=True, help_text="user name")
    authority_designation = models.CharField(max_length=200, null=True, blank=True, help_text="approver role")
    sla_days = models.PositiveIntegerField(default=7)
    sla_due_date = models.DateField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    
    class Meta:
        db_table = "incentive_approval_history"



class IncentiveCafNumberGenerator(models.Model):
    caf_number = models.CharField(max_length=30, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "incentive_caf_number_generator"


class IncentiveSlecOrder(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_slec_order"
    )
    unit_name = models.CharField(max_length=255, null=True, blank=True, help_text="Company Name")
    constitution_type_name = models.CharField(max_length=100, null=True, blank=True, help_text="Constitution Type Name")
    constitution_type = models.ForeignKey(
        OrganizationType, on_delete=models.CASCADE, null=True, blank=True, related_name="slec_order_org_id"
    )
    unit_type = models.CharField(max_length=60, null=True, blank=True, help_text="unit_type")
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, null=True, blank=True, related_name="slec_activity"
    )
    activity_name = models.CharField(max_length=50, null=True, blank=True, help_text="activity name")
    sector = models.ForeignKey(
        Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="slec_sector"
    )
    sector_name = models.CharField(max_length=200, null=True, blank=True, help_text="Sector name")
    sub_sector = models.ForeignKey(
        SubSector, on_delete=models.CASCADE, null=True, blank=True, related_name="slec_sub_sector"
    )
    sub_sector_name = models.TextField(null=True, blank=True, help_text="Sub Sector name")
    category_of_block = models.CharField(max_length=15, null=True, blank=True, help_text="Priority or Non Priority")
    date_of_slec_meeting = models.DateField(null=True, blank=True, help_text="Date of Slec meeting")
    slec_meeting_number = models.CharField(max_length=100, null=True, blank=True, help_text="Slec meeting number")
    eligible_investment_plant_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bipa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    yearly_bipa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligibility_from = models.DateField(null=True, blank=True, help_text="elegibility from")
    eligibility_to = models.DateField(null=True, blank=True, help_text="elegibility to")
    remark = models.TextField(null=True, blank=True, help_text="Remark")
    name_of_authority = models.CharField(max_length=200, null=True, blank=True, help_text="user name")
    authority_designation = models.CharField(max_length=200, null=True, blank=True, help_text="approver designation")
    status = models.CharField(max_length=30, null=True, blank=True, help_text="slec order pending")
    commencement_date = models.DateField(null=True, blank=True, help_text="commencement date")

    class Meta:
        db_table = "incentive_slec_order"


class IncentiveSlecProduct(models.Model):
    slec_order = models.ForeignKey(
        IncentiveSlecOrder, on_delete=models.CASCADE, null=True, blank=True, related_name="slec_product"
    )
    measurement_unit = models.ForeignKey(
        MeasurementUnitList, on_delete=models.CASCADE, related_name="slec_measurement", null=True, blank= True
    )
    measurement_unit_name = models.CharField(max_length=255, null=True, blank= True, help_text="Measurement unit names")
    product_name = models.TextField(null=True, blank= True, help_text="Product Name")
    total_annual_capacity = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="Annual Capacity")
    comm_production_date = models.DateField(null=True, blank= True, help_text="Commercial Production Date")

    class Meta:
        db_table = "incentive_slec_products"


class IncentiveSlecYealy(models.Model):
    slec_order = models.ForeignKey(
        IncentiveSlecOrder, on_delete=models.CASCADE, null=True, blank=True, related_name="slec_yearly_incentive"
    )
    incentive_year = models.CharField(max_length=10, null=True, blank=True, help_text="incentive year")
    status = models.CharField(max_length=10, null=True, blank=True, help_text="Paid and Unpaid")
    claim_year_serial_number = models.CharField(max_length=4, null=True, blank=True, help_text="1,2,3")
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank= True, help_text="Incentive")
    remark = models.CharField(max_length=255, null=True, blank=True, help_text="Remarks")
    
    class Meta:
        db_table = "incentive_slec_year"

class SectorDocumentList(TimeStampModel):
    document = models.ForeignKey(
        DocumentList, on_delete=models.CASCADE, related_name="in_sector_specific_documents"
    )
    sector = models.ForeignKey(
        Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="doc_sector"
    )
    doc_type = models.CharField(max_length=50, default="Common", help_text="Common, GIA etc")
    status = models.CharField(max_length=10, default="active", help_text="active or inactive etc")
    
    class Meta:
        db_table = "incentive_document_sector_list"

class SectorIncentiveList(models.Model):
    sector = models.ForeignKey(
        Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="incentive_sector_list"
    )
    main_header = models.CharField(max_length=100, null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    icon_message = models.TextField(null=True, blank=True)
    input_tag = models.CharField(max_length=50, null=True, blank=True)
    input_type = models.CharField(max_length=20, null=True, blank=True)
    input_options = models.TextField(null=True, blank=True)
    display_options = models.BooleanField(default=True)
    placeholder = models.CharField(max_length=255, null=True, blank=True)
    display_order = models.SmallIntegerField(default=999)
    status = models.CharField(max_length=10, default="active", help_text="active or inactive etc")
    
    class Meta:
        db_table = "calculator_incentive_sector_list"

class InCAFExpansion(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_expansion"
    )
    date_of_production = models.DateField(blank=True, null=True, help_text="Commercial Production Date")
    expansion_no = models.SmallIntegerField(default=1)
    period_from = models.DateField(blank=True, help_text="Period From Date", null=True)
    period_to = models.DateField(blank=True, help_text="Period to Date", null=True)
    total_investment_land = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    investment_in_building = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    investment_in_plant_machinery = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    total_investment_electrical = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    total_investment_other_asset = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    total_investment_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    turnover = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)

    class Meta:
        db_table = "incentive_caf_expansion_details"

class InCAFExpansionProduct(TimeStampModel):
    expansion = models.ForeignKey(
        InCAFExpansion, on_delete=models.CASCADE, blank=True, null=True, related_name="expansion_products"
    )
    measurement_unit = models.ForeignKey(
        MeasurementUnitList, on_delete=models.CASCADE, related_name="incaf_expansion_measurement", null=True, blank= True
    )
    measurement_unit_name = models.CharField(max_length=255, null=True, blank= True, help_text="Measurement unit names")
    other_measurement_unit_name = models.CharField(max_length=255, null=True, blank= True, help_text="Measurement unit names")
    product_name = models.TextField(null=False, blank=False, help_text="Product Name")
    annual_capacity_before_expansion = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="Capacity befor expansion")
    annual_capacity_during_expansion = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="Capacity during expansion")
    total_annual_capacity = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank= True, help_text="Annual Capacity")
    
    class Meta:
        db_table = "incentive_caf_expansion_product_details"

class InCAFSLECDocument(TimeStampModel):
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="incaf_slec_document"
    )
    slec_doc_name = models.CharField(max_length=255, null=True, blank=True, help_text="Doc Name")
    slec_doc_path = models.TextField(null=True, blank=True, help_text="Document Path")
    slec_order = models.ForeignKey(
        IncentiveSlecOrder, on_delete=models.CASCADE, related_name="incaf_slec_document", null=True, blank=True
    )
    
    class Meta:
        db_table = "incentive_caf_slec_documents"

class IncentiveClaimBasic(models.Model):
    id = models.BigAutoField(primary_key=True)
    year_of_claimed_assistance = models.CharField(max_length=255, null=True, blank=True)
    employees_permanent_resident_of_mp = models.IntegerField(null=True, blank=True)
    employees_outside_of_mp = models.IntegerField(null=True, blank=True)
    total_employees = models.IntegerField(null=True, blank=True)
    apply_date = models.DateTimeField()
    action_date = models.DateTimeField()
    action_by_id = models.BigIntegerField()
    action_by_name = models.CharField(max_length=255)
    incentive_slec_year = models.ForeignKey(
        IncentiveSlecYealy, on_delete=models.CASCADE, related_name="claim_incentive_year", null=True, blank=True
    )
    claim_pdf_url = models.CharField(max_length=500, null=True, blank=True)
    acknowledgement_date = models.DateTimeField(null=True, blank=True)
    acknowledgement = models.BooleanField(null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'incentive_claim_basic'

class IncentiveSanctionOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    incentive_caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, related_name="sanction_caf", null=True, blank=True
    )
    incentive_claim = models.ForeignKey(
        IncentiveClaimBasic, on_delete=models.CASCADE, related_name="sanction_claim", null=True, blank=True
    )
    sanction_order_no = models.CharField(max_length=250, null=True, blank=True)
    sanction_order_created_date = models.DateField(null=True, blank=True)
    unit_name = models.CharField(max_length=250, null=True, blank=True)
    location_of_unit = models.CharField(max_length=100, null=True, blank=True)
    annual_yearly_investment_assistance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    gross_supply_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    geographical_multiple = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    employement_multiple_for_the_claim_year = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    export_multiple_for_the_claim_year = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_sanctioned_assistance_amount_till_previous_year = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_sanctioned_assistance_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sanction_order_create_by = models.BigIntegerField(null=True, blank=True)
    sanction_order_create_by_name = models.CharField(max_length=100, null=True, blank=True)
    action_by = models.BigIntegerField(null=True, blank=True)
    action_by_name = models.CharField(max_length=100, null=True, blank=True)
    action_date = models.DateField(null=True, blank=True)
    sanction_order_esign_date = models.DateField(null=True, blank=True)
    sanction_order_final_pdf_id = models.BigIntegerField(null=True, blank=True)
    sanction_order_creation_pdf_id = models.BigIntegerField(null=True, blank=True)
    sanction_order_gm_pdf_id = models.BigIntegerField(null=True, blank=True)
    sanction_order_cgm_pdf_id = models.BigIntegerField(null=True, blank=True)
    type_of_unit = models.CharField(max_length=250, null=True, blank=True)
    sanction_pdf_url = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    acknowledgement_date = models.DateField(null=True, blank=True)
    acknowledgement = models.BooleanField(null=True, blank=True)
    is_old_record = models.BooleanField(null=True, blank=True)
    intention = models.ForeignKey(
        CustomerIntentionProject, on_delete=models.CASCADE, related_name="sanction_intention", null=True, blank=True
    )
    year_of_claimed_assistance = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'incentive_sanction_order'


class IncentiveDisbursement(models.Model):
    id = models.BigAutoField(primary_key=True)
    disbursement_date = models.DateField(null=True, blank=True)
    disbursed_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    intention = models.ForeignKey(
        CustomerIntentionProject, on_delete=models.CASCADE, related_name="disbursement_intention", null=True, blank=True
    )
    incentive_sanction_order = models.ForeignKey(
        IncentiveSanctionOrder, on_delete=models.CASCADE, related_name="disbursement_sanction", null=True, blank=True
    )
    year_of_claimed_assistance = models.CharField(max_length=255, null=True, blank=True)
    action_by = models.BigIntegerField(null=True, blank=True)
    action_by_name = models.CharField(max_length=255, null=True, blank=True)
    action_date = models.DateField(null=True, blank=True)

    class Meta:
        managed = False 
        db_table = 'incentive_disbursement'

class IncentiveClaimProductDetail(models.Model):
    id = models.BigAutoField(primary_key=True)
    incentive_slec_product =  models.ForeignKey(
        IncentiveSlecProduct, on_delete=models.CASCADE, related_name="claims_slec_product", null=True, blank=True
    )
    production_quantity = models.IntegerField(null=True, blank=True)
    production_amount = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    sale_quantity = models.IntegerField(null=True, blank=True)
    sale_amount = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    export_quantity = models.IntegerField(null=True, blank=True)
    export_amount = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    gsm_percentage = models.FloatField(null=True, blank=True)
    gsm_final_value = models.FloatField(null=True, blank=True)
    export_percentage = models.FloatField(null=True, blank=True)
    export_final_value = models.FloatField(null=True, blank=True)
    apply_date = models.DateTimeField(null=True, blank=True)
    action_date = models.DateTimeField(null=True, blank=True)
    action_by_id = models.BigIntegerField(null=True, blank=True)
    action_by_name = models.CharField(max_length=255, null=True, blank=True)
    incentive_claim_basic = models.ForeignKey(
        IncentiveClaimBasic, on_delete=models.CASCADE, related_name="claim_basic", null=True, blank=True
    )
    measurement_unit_name = models.CharField(max_length=255, null=True, blank=True)
    measurement_unit = models.ForeignKey(
        MeasurementUnitList, on_delete=models.CASCADE, related_name="claim_measurement", null=True, blank= True
    )
    total_annual_capacity = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'incentive_claim_product_details'

class IncentiveOfflineApplications(TimeStampModel):
    intention_id = models.CharField(max_length=100, null=True, blank=True)
    intention_date = models.DateField(null=True, blank=True)
    unit_name = models.CharField(max_length=255,null=True, blank=True)
    date_of_production = models.DateField(null=True, blank=True)
    unit_type = models.CharField(max_length=100, null=True, blank=True)
    activity = models.CharField(max_length=100, null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    block_priority = models.CharField(max_length=100, null=True, blank=True)
    slec_meeting_date = models.DateField(null=True, blank=True)
    slec_meeting_no = models.CharField(max_length=100, null=True, blank=True)
    eligible_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bipa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ybipa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligibility_start_date = models.DateField(null=True, blank=True)
    eligibility_end_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = "incentive_offline_applications"

class IPAUnitDataMaster(models.Model):
    id = models.IntegerField(primary_key=True, db_column='S._No.')
    intention_id = models.TextField(db_column='Intention_ID', null=True, blank=True)
    intention_date = models.TextField(db_column='Intention Date', null=True, blank=True)
    unit_name = models.TextField(db_column='Unit  Name', null=True, blank=True)
    unit_type = models.TextField(db_column='Type', null=True, blank=True)
    date_of_production = models.TextField(db_column='Date of Production', null=True, blank=True)
    sector = models.TextField(db_column='Sector', null=True, blank=True)
    product_name = models.TextField(db_column='Product Name',null=True, blank=True)
    block_priority = models.TextField(db_column='Priority Block (Y/N)', null=True, blank=True)
    slec_meeting_no = models.TextField(db_column='SLEC Meeting Number',null=True, blank=True)
    slec_meeting_date = models.TextField(db_column='SLEC Meeting Date', null=True, blank=True)
    eligibility_start_date = models.TextField(db_column='Eligibility Period Start',null=True, blank=True)
    eligibility_end_date = models.TextField(db_column='Eligibility Period End', null=True, blank=True)
    eligible_investment = models.IntegerField(db_column='Eligible Investment Rs. In Lakh.', null=True, blank=True)
    bipa = models.IntegerField(db_column='Basic IPA Rs. In Lakh', null=True, blank=True)
    ybipa = models.IntegerField(db_column='Yearly BIPA',null=True, blank=True)
    claim_fy = models.TextField(db_column='Claim FY', null=True, blank=True)
    sanctioned_date = models.TextField(db_column='Sanctioned Date',null=True, blank=True)
    sanctioned_amount = models.FloatField(db_column='Sanctioned Amount  (IN Lakh)',null=True, blank=True)
    disbursement_date = models.TextField(db_column='Disbursement Date', null=True, blank=True)
    disbursed_amount = models.IntegerField(db_column='Disbursed Amount (In Lakh)', null=True, blank=True)
    remark = models.TextField(db_column='Remark', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'IPA_Unit_Data_Master'

class IncentiveDepartmentQueryModel(TimeStampModel):
    intention = models.ForeignKey(
        CustomerIntentionProject, on_delete=models.CASCADE, related_name="query_intention_id"
    )
    query_type = models.CharField(max_length=30, null=True, blank=True, help_text="In-Progress, Completed, Deleted")
    status = models.CharField(max_length=100, null=True, blank=True, help_text="In-Progress, Completed, Deleted")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="incentive_query_user")
    user_name = models.CharField(max_length=255, null=True, blank=True, help_text="name of user")
    depratment_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="incentive_query_department_user")
    department_user_name = models.CharField(max_length=255, null=True, blank=True, help_text="department user name")
    department_user_role =  models.ForeignKey(
        Role, on_delete=models.CASCADE, null=True, blank=True, related_name="query_user_role"
    )
    user_remark = models.TextField(null=True, blank=True, help_text="User Remark")
    department_remark = models.TextField(null=True, blank=True, help_text="Department Remark")
    caf = models.ForeignKey(
        IncentiveCAF, on_delete=models.CASCADE, null=True, blank=True, related_name="query_caf"
    )
    
    class Meta:
        db_table = "incentive_department_queries"

class IncentiveQueryDocumentModel(TimeStampModel):
    query = models.ForeignKey(
        IncentiveDepartmentQueryModel, on_delete=models.CASCADE, related_name="queries"
    )
    document_name = models.CharField(max_length=255, null=True, blank=True, help_text="document path")
    document_path = models.TextField(null=True, blank=True, help_text="document path")
    
    class Meta:
        db_table = "incentive_query_documents"



class IncentiveSLECArrearModel(TimeStampModel):
    slec_order = models.ForeignKey(
        IncentiveSlecOrder, on_delete=models.CASCADE, null=True, blank=True, related_name="arrear_slec_order"
    )
    incentive_year = models.CharField(max_length=10, null=True, blank=True, help_text="incentive year")
    status = models.CharField(max_length=100, null=True, blank=True, help_text="In-Progress, Completed, Deleted")
    depratment_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="slec_arrear_department_user"
    )
    department_user_name = models.CharField(max_length=255, null=True, blank=True, help_text="department user name")
    department_user_role =  models.ForeignKey(
        Role, on_delete=models.CASCADE, null=True, blank=True, related_name="arrear_user_role"
    )
    department_remark = models.TextField(null=True, blank=True, help_text="Department Remark")
    
    class Meta:
        db_table = "incentive_slec_order_arrears"

class IncentiveTypeMasterModel(TimeStampModel):
    incentive_type = models.CharField(max_length=50, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, default="active", help_text="active or inactive etc")
    incentive_validity = models.CharField(max_length= 20, null=True, blank=True)
    
    class Meta:
        db_table = "incentive_type_master"

class IncentiveTypeSectorModel(TimeStampModel):
    incentive_type = models.ForeignKey(IncentiveTypeMasterModel, on_delete=models.CASCADE, null=False)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="incentive_type_sectors", null=True, blank=True)
    display_order = models.IntegerField (null= True,blank= True)
    show_in_incentive = models.BooleanField(default=False)
    show_in_claim = models.BooleanField(default=False)
    
    class Meta:
        db_table = "incentive_type_based_on_sector"

class AgendaInvestmentModel(TimeStampModel):
    agenda = models.ForeignKey(
        IncentiveAgenda, on_delete=models.CASCADE, related_name="agenda_investment"
    )
    is_ccip = models.BooleanField(default= False)
    turnover = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    is_export_unit = models.BooleanField(default=False)
    is_csr = models.BooleanField(default= False)
    csr = models.CharField(max_length=100, null=True, blank=True)
    is_fdi = models.BooleanField(default=False)
    promoters_equity_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    term_loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fdi_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fdi_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_finance_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_building = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligible_investment_building = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_plant_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligible_investment_plant_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_inhouse_rnd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligible_investment_inhouse_rnd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True) 
    investment_captive_power = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligible_investment_captive_power = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_energy_saving_devices = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligible_investment_energy_saving_devices = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_imported_second_hand_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligible_investment_imported_second_hand_machinery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_refurbishment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eligible_investment_refurbishment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_furniture_fixtures = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)

    class Meta:
        db_table = "incentive_agenda_investment"


class AgendaIncentiveModel(TimeStampModel):
    agenda = models.ForeignKey(
        IncentiveAgenda, on_delete=models.CASCADE, related_name="agenda_incentive"
    )
    incentive_json = models.JSONField(null=True, blank=True, help_text="store json data")
    
    class Meta:
        db_table = "incentive_agenda_assistance"

class CcipIndustrialUnitGeneralInfo(models.Model):
    id = models.BigAutoField(primary_key=True)  # bigint with sequence
    intention_to_invest_number = models.CharField(max_length=50, blank=True, null=True)
    request_date = models.DateField(blank=True, null=True)
    name_of_industrial_unit = models.CharField(max_length=255, blank=True, null=True)
    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    constitution_type_id = models.BigIntegerField(blank=True, null=True)  # FK to organization_type.id
    constitution_name = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    address_line = models.CharField(max_length=500, blank=True, null=True)
    district_id = models.BigIntegerField(blank=True, null=True)  # FK to sws_district.id
    district_name = models.CharField(max_length=80, blank=True, null=True)
    city_id = models.BigIntegerField(blank=True, null=True)
    city_name = models.CharField(max_length=50, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    category_of_block = models.CharField(max_length=50, blank=True, null=True)
    action_by_id = models.BigIntegerField(blank=True, null=True)
    action_by_name = models.CharField(max_length=150, blank=True, null=True)
    action_date = models.DateField(blank=True, null=True)
    doc_url = models.CharField(max_length=1000, blank=True, null=True)
    signed_doc_url = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ccip_industrial_unit_general_info'