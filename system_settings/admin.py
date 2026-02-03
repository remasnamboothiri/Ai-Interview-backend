from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import SystemSetting

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['id', 'setting_key', 'setting_value', 'data_type', 'is_public', 'updated_at']
    list_filter = ['data_type', 'is_public', 'updated_at']
    search_fields = ['setting_key', 'description']
