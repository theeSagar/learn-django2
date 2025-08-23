from operator import mod
from django.db import models
from authentication.models import User
from sws.models import (
    Sector,
    SubSector,
    DepartmentList,
    IndustrialAreaList,
    CAF,
)

class ApprovalList(models.Model):
    name = models.CharField(max_length=255, default="")
    description = models.TextField(default="")
    phase = models.CharField(max_length=40, default="")
    timelines = models.CharField(max_length=40, default="")
    TYPE_CHOICES = [
        ("service", "Services"),
        ("clearance", "Clearance")
    ]
    approval_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="clearance")
    instruction = models.CharField(max_length=255, default="", blank=True, null=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table='kya_approval_lists'

class SectorApprovalMapping(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="sector_clearance")
    approval = models.ForeignKey(ApprovalList, on_delete=models.CASCADE, null=True, blank=True, related_name="approval_clearance")
    TYPE_CHOICES = [
        ("mandatory", "Mandatory"),
        ("optional", "Optional")
    ]
    approval_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="optional")
    display_order = models.IntegerField(default=9999)

    class Meta:
        db_table='kya_sector_clearance_mappings'

class SubSectorApprovalMapping(models.Model):
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE, null=True, blank=True, related_name="subsector_clearance")
    approval = models.ForeignKey(ApprovalList, on_delete=models.CASCADE, null=True, blank=True, related_name="approval_sub_clearance")
    TYPE_CHOICES = [
        ("mandatory", "Mandatory"),
        ("optional", "Optional")
    ]
    approval_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="optional")
    display_order = models.IntegerField(default=9999)

    class Meta:
        db_table='kya_subsector_clearance_mappings'

class IAExemptionMapping(models.Model):
    industrial_area = models.ForeignKey(IndustrialAreaList, on_delete=models.CASCADE, null=True, blank=True, related_name="industrial_area_list_clearance")
    approval = models.ForeignKey(ApprovalList, on_delete=models.CASCADE, null=True, blank=True, related_name="approval_ia_clearance")

    class Meta:
        db_table='kya_industryarea_exemption_mappings'

class UserCAFService(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    caf = models.ForeignKey(
        CAF, on_delete=models.CASCADE, related_name="caf_services"
    )
    approval = models.ForeignKey(
        ApprovalList, on_delete=models.CASCADE, related_name="caf_approvals"
    )
    service_name = models.CharField(max_length=255, null=True, blank=True)
    department_name = models.TextField(null=True, blank=True)
    phase = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    request_number = models.CharField(max_length=100, null=True, blank=True)
    request_json = models.TextField(null=True, blank=True)
    department = models.ForeignKey(DepartmentList, on_delete=models.CASCADE, related_name="department_user_service", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='caf_user_services'

class KYAQuestionBank(models.Model):
    question_tag = models.CharField(max_length=100, null=True, blank=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, null=True, blank=True, help_text="Values are dropdown, radio, combobox etc")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kya_question_bank'

class KYAQuestionBankOption(models.Model):
    option_value = models.CharField(max_length=100, null=True, blank=True)
    option_display_name = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'kya_question_bank_options'

class SectorQuestionMapping(models.Model):
    question = models.ForeignKey(
        KYAQuestionBank, on_delete=models.CASCADE, related_name="sqm_questions"
    )
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="sqm_sector")
    TYPE_CHOICES = [
        ("mandatory", "Mandatory"),
        ("mandatory_question", "Mandatory Questions"),
        ("optional", "Optional"),
        ("service", "Service"),
        ("service_question", "Service Questions"),
    ]
    approval_type = models.CharField(max_length=100, choices=TYPE_CHOICES, default="optional")
    MODE_CHOICES = [
        ("static", "Static"),
        ("dynamic", "Dynamic")
    ]
    mode = models.CharField(max_length=40, choices=MODE_CHOICES, default="dynamic")
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "In-Active"),
        ("deleted", "Deleted")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    display_order = models.IntegerField(default=9999)
    next_question_tag = models.CharField(max_length=100, default="")

    class Meta:
        db_table = 'kya_sector_question_mappings'

class SectorQuestionMethod(models.Model):
    sector_question = models.ForeignKey(
        SectorQuestionMapping, on_delete=models.CASCADE, related_name="sqmethod_questions"
    )
    method = models.CharField(max_length=100, blank=True, null=True)
    target = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'kya_sector_question_methods'

class SectorQuestionOption(models.Model):
    sector_question = models.ForeignKey(
        SectorQuestionMapping, on_delete=models.CASCADE, related_name="sector_questions"
    )
    question_options = models.ForeignKey(
        KYAQuestionBankOption, on_delete=models.CASCADE, related_name="sector_question_options"
    )
    display_order = models.IntegerField(default=9999)
    next_question_tag = models.CharField(max_length=100, default="")

    class Meta:
        db_table = 'kya_sector_question_options'

class SectorQuestionApproval(models.Model):
    sector_question = models.ForeignKey(
        SectorQuestionMapping, on_delete=models.CASCADE, related_name="sqam_questions"
    )
    question_tag = models.CharField(max_length=100, null=True, blank=True)
    question_output = models.CharField(max_length=100, null=True, blank=True)
    approval = models.ForeignKey(
        ApprovalList, on_delete=models.CASCADE, related_name="sqam_approvals"
    )

    class Meta:
        db_table = 'kya_sector_question_approvals'

class SubSectorQuestionMapping(models.Model):
    question = models.ForeignKey(
        KYAQuestionBank, on_delete=models.CASCADE, related_name="ssqm_questions"
    )
    subsector = models.ForeignKey(
        SubSector, on_delete=models.CASCADE, null=True, blank=True, related_name="ssqm_subsector"
    )
    TYPE_CHOICES = [
        ("mandatory", "Mandatory"),
        ("mandatory_question", "Mandatory Question"),
        ("optional", "Optional")
    ]
    approval_type = models.CharField(max_length=100, choices=TYPE_CHOICES, default="optional")
    MODE_CHOICES = [
        ("static", "Static"),
        ("dynamic", "Dynamic")
    ]
    mode = models.CharField(max_length=40, choices=MODE_CHOICES, default="dynamic")
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "In-Active"),
        ("deleted", "Deleted")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    next_question_tag = models.CharField(max_length=100, default="")
    display_order = models.IntegerField(default=9999)

    class Meta:
        db_table = 'kya_subsector_question_mappings'

class SubSectorQuestionMethod(models.Model):
    subsector_question = models.ForeignKey(
        SubSectorQuestionMapping, on_delete=models.CASCADE, related_name="ssqmethod_questions"
    )
    method = models.CharField(max_length=100, blank=True, null=True)
    target = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'kya_subsector_question_methods'

class SubSectorQuestionOption(models.Model):
    subsector_question = models.ForeignKey(
        SubSectorQuestionMapping, on_delete=models.CASCADE, related_name="ssqo_questions"
    )
    question_options = models.ForeignKey(
        KYAQuestionBankOption, on_delete=models.CASCADE, related_name="ssqo_options"
    )
    display_order = models.IntegerField(default=9999)
    next_question_tag = models.CharField(max_length=100, default="")

    class Meta:
        db_table = 'kya_subsector_question_options'

class SubSectorQuestionApproval(models.Model):
    subsector_question = models.ForeignKey(
        SubSectorQuestionMapping, on_delete=models.CASCADE, related_name="ssqm_questions"
    )
    question_tag = models.CharField(max_length=100, null=True, blank=True)
    question_output = models.CharField(max_length=100, null=True, blank=True)
    approval = models.ForeignKey(
        ApprovalList, on_delete=models.CASCADE, related_name="ssqm_approvals"
    )

    class Meta:
        db_table = 'kya_subsector_question_approvals'

class ApprovalDepartmentList(models.Model):
    approval = models.ForeignKey(ApprovalList, on_delete=models.CASCADE, related_name="adl_approval")
    department = models.ForeignKey(DepartmentList, on_delete=models.CASCADE, related_name="adl_department")
    criteria = models.CharField(max_length=100, default="")
    status = models.BooleanField(default=True)

    class Meta:
        db_table='kya_approval_departments'

class UserApprovals(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="user_approval_sector")
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE, null=True, blank=True, related_name="user_approval_subsector")
    line_of_business = models.CharField(max_length=100, blank=True, null=True)
    scale_of_industry = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table='kya_user_approvals'

class UserApprovalItems(models.Model):
    user_approval = models.ForeignKey(UserApprovals, on_delete=models.CASCADE, null=True)
    approval = models.ForeignKey(ApprovalList, on_delete=models.CASCADE, null=True, blank=True, related_name="user_approval_data")

    class Meta:
        db_table='kya_user_approval_items'


class SectorCriteriaHideApproval(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, null=True, blank=True, related_name="sector_hide_approvals")
    approval = models.ForeignKey(ApprovalList, on_delete=models.CASCADE, null=True, blank=True, related_name="approval_hide")
    criteria = models.CharField(max_length=100, blank=False)
    output = models.CharField(max_length=100, blank=False)

    class Meta:
        db_table='kya_sector_criteria_hide_approvals'

class ApprovalConfigurationModel(models.Model):
    approval = models.ForeignKey(ApprovalList, on_delete=models.CASCADE, null=True, blank=True, related_name="approval_configs")
    redirect_url = models.TextField(null=True, blank=True)
    signing_url = models.TextField(null=True, blank=True)
    request_method = models.CharField(max_length=10, blank=True, null=True)
    request_params = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table='kya_service_configs'
    
