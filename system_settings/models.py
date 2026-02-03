from django.db import models

# Create your models here.
from django.db import models
from users.models import User

class SystemSetting(models.Model):
    DATA_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]
    
    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    data_type = models.CharField(max_length=20, choices=DATA_TYPES, default='string')
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='settings_updated')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='settings_created')
    
    class Meta:
        db_table = 'system_settings'
        ordering = ['setting_key']
    
    def __str__(self):
        return f"{self.setting_key}: {self.setting_value}"
