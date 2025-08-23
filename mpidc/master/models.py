from django.db import models

# Create your models here.
class ConfigurationsModel(models.Model):
    parameter_name = models.CharField(max_length=100, null=True, blank=True)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_configurations"