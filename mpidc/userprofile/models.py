from django.db import models
from django.utils import timezone
from authentication.models import *
from sws.models import Activity, Sector, District, State


class OrganizationType(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False, default="")
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organization_type"


class UserOrgazination(models.Model):
    user_profile = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    organization_type = models.ForeignKey(
        OrganizationType, on_delete=models.CASCADE, null=True
    )
    name = models.CharField(max_length=255, default="")
    registered_under_msme = models.BooleanField(default=False)
    msme_registration_number = models.CharField(max_length=255, blank=True, null=True)
    firm_registration_number = models.CharField(max_length=255, default="")
    registration_date = models.DateField()
    scale_of_industry = models.CharField(max_length=255, blank=True, null=True)
    firm_pan_number = models.CharField(max_length=10, default="")
    firm_gstin_number = models.CharField(max_length=15, default="")
    website_url = models.CharField(max_length=50, default="")
    helpdesk_number = models.CharField(max_length=50, default="")
    firm_email_id = models.CharField(max_length=100, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    date_of_incorporation = models.CharField(max_length=255, blank=True, null=True)
    pan_verify = models.BooleanField(default=False)
    class Meta:
        db_table = "user_organization"

class OrganizationUserModel(models.Model):
    organization = models.ForeignKey(
        UserOrgazination,
        on_delete=models.CASCADE,
        null=True,
        related_name="organization_users",
    )
    name = models.CharField(max_length=255, default="")
    mobile_number = models.CharField(max_length=15, default="")
    email_id = models.CharField(max_length=100, default="")
    contact_type = models.CharField(
        max_length=40, default="", null=True, blank=True 
    )
    country_code = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    designation = models.CharField(max_length=50, null=True, blank=True)
    other_designation = models.CharField(max_length=50,null=True,blank=True)

    class Meta:
        db_table = "organization_user_contact_detail"

class OrganizationAddress(models.Model):
    ADDRESS_TYPES = (
        ("Registered", "Registered Office"),
        ("Communication", "Communication"),
    )

    organization = models.ForeignKey(
        UserOrgazination,
        on_delete=models.CASCADE,
        null=True,
        related_name="org_address",
    )
    address_line = models.CharField(max_length=255, default="")
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        null=True,
        related_name="org_address_district",
    )
    pin_code = models.CharField(max_length=6, default="")
    state = models.ForeignKey(
        State, on_delete=models.CASCADE, null=True, related_name="org_address_state"
    )
    address_type = models.CharField(
        max_length=20, choices=ADDRESS_TYPES, default="Registered"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_organization_address"


class UserBankDetails(models.Model):
    STATUS_CHOICES = [
        ("active", "active"),
        ("inactive", "inactive"),
        ("blocked", "blocked"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    bank_name = models.CharField(max_length=50, blank=True, null=True)
    bank_branch = models.CharField(max_length=255, blank=True, null=True)
    bank_address = models.CharField(max_length=255, blank=True, null=True)
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    bank_ifsc_code = models.CharField(max_length=11, blank=True, null=True)
    account_number = models.CharField(max_length=18, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

    class Meta:
        db_table = "user_bank_details"


class ServiceTracker(models.Model):
    STATUS_CHOICES = [
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("in-process", "In-process"),
        ("objection", "Objection"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    service_name = models.CharField(max_length=255, blank=True, null=True)
    application_no = models.CharField(max_length=255, blank=True, null=True)
    department_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="in-process"
    )
    pan_no = models.CharField(max_length=10, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "service_tracker"


class UserProfilePDF(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_profile_pdf"
    )
    user_pdf_file=models.CharField(max_length=255,blank=True, null=True)
    doc_url = models.CharField(max_length=255,blank=True, null=True)

    class Meta:
        db_table = "user_profile_pdf"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        db_table = "user_notification"

class ExceptionLog(models.Model):
    api_name = models.CharField(max_length=255)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exception_logs"
