from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import InterviewData

@admin.register(InterviewData)
class InterviewDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'interview', 'session_number', 'status', 'started_at', 'ended_at']
    list_filter = ['status', 'is_primary_session']
    search_fields = ['interview__id', 'candidate_ip']
