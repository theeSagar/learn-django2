from datetime import date
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractUser, User
from sws.models import Designation



# Create your models here.

class Country(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False)
    name = models.CharField(max_length=100, blank=False, null=False)
    iso = models.CharField(max_length=10, blank=False, null=False)

    class Meta:
        db_table = "tbl_countries"
    

class CustomUserProfile(models.Model):
    user_type_choices = [
        ('admin', 'Admin'),
        ('regular', 'Regular'),
        ('guest', 'Guest'),
    ]
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    country_code = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)
    document_folder = models.CharField(max_length=70, null=True, blank=True)
    mobile_no = models.CharField(max_length=13, null=True, blank=True, default=None)
    user_type = models.CharField(max_length=10, choices=user_type_choices, default='regular')
    mode_of_registration_choices = [
        ('online', 'Online'),
        ('guest', 'Guest'),
        ('offline', 'Offline'),
    ]
    mode_of_registration = models.CharField(max_length=10, choices=mode_of_registration_choices, default='online')
    alternate_email_id = models.CharField(max_length=50, default="")
    designation = models.ForeignKey(Designation, null=True, blank=True, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    status_type = [
        ('active', 'Active'),
        ('block', 'Block'),
        ('inactive', 'In-Active'),
    ]
    status = models.CharField(max_length=10, choices=status_type, default='active')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True, default=None)
    dob = models.DateField(null=True, blank=True, default=None)
    father_name = models.CharField(max_length=255, null=True, blank=True, default=None)
    pan_card_number = models.CharField(max_length=10, null=True, blank=True, default=None)
    pan_verify = models.BooleanField(default=False)
    email_verify = models.BooleanField(default= True)
    is_blocked = models.BooleanField(default=False)
    wrong_otp_attempts = models.IntegerField(default=0)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    class Meta:
        db_table = "user_profile"

class UserProfileStatus(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    is_profile_completed = models.BooleanField(default=False)
    
    class Meta:
        db_table = "user_profile_status"

class DigiLockerSession(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "auth_digilocker_sessions"

class Role(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    role_name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    description = models.TextField(default="", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.role_name

    class Meta:
        db_table = "project_roles"

class Permission(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=100, unique=True, blank=False, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.name

    class Meta:
        db_table = "project_permissions"

class UserHasRole(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.CASCADE)
    role_type = models.CharField(max_length=20, null=False, default="primary", blank=False, help_text="primary, secondary")

    def __str__(self):
        return f"{self.user.username} - {self.role.role_name}"

    class Meta:
        db_table = "project_user_has_roles"
        unique_together = ('user', 'role')  


class Module(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    module_name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    description = models.TextField(default="", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.module_name

    class Meta:
        db_table = "project_modules"


class RoleModulePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "project_role_module_permissions"
        unique_together = ('role', 'module', 'permission')

    def __str__(self):
        return f"{self.role.role_name} - {self.module.module_name} - {self.permission.name}"


class UserModulePermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "project_user_module_permissions"
        unique_together = ('user', 'module', 'permission')

    def __str__(self):
        return f"{self.user.username} - {self.module.module_name} - {self.permission.name}"
    

class WorkflowList(models.Model):
    flow_type = models.CharField(max_length=20, help_text="claim, incentive etc")
    level_no = models.SmallIntegerField()
    current_role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="wf_current_role")
    current_status = models.CharField(max_length=150, null=True, blank=True, help_text="Pending from Manager action etc")
    sla_period = models.IntegerField(null=True, blank=True, help_text="SLA Period")

    class Meta:
        db_table = "project_workflow"

class WorkflowItemList(models.Model):
    workflow = models.ForeignKey(WorkflowList, null=False, blank=False, on_delete=models.CASCADE)
    next_role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True, related_name="wf_next_role")
    next_flow_type = models.CharField(max_length=20, null=True, blank=True, help_text="claim, incentive etc")
    action_type = models.CharField(max_length=40, null=True, blank=True, help_text="Forward to next level")
    status = models.CharField(max_length=100, null=True, blank=True, help_text="Pending from GM action etc")

    class Meta:
        db_table = "project_workflow_items"

class WebAppointmentModel(models.Model):
    
    name = models.CharField(max_length=255, null=True, blank=True , default=None)
    company_name = models.CharField(max_length=255, null=True, blank=True, default=None)
    designation_name = models.CharField(max_length=255 , null=True,blank=True, default=None)
    mobile_no = models.CharField(max_length=13, null=True, blank=True , default=None)
    email = models.EmailField(null=True, blank=True, default=None)
    appointment_with = models.CharField(max_length=255 , null=True,blank=True , default=None) 
    date_of_appointment = models.DateField(blank=True, null=True)
    meeting_reason = models.CharField(max_length=255,null=True, blank=True, default=None) 
    description = models.TextField(null=True, blank=True, default=None)
    status = models.CharField(max_length=50,default="New")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "web_appointment_form"
