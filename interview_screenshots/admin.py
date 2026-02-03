from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import InterviewScreenshot


@admin.register(InterviewScreenshot)
class InterviewScreenshotAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'interview',
        'screenshot_number',
        'timestamp',
        'multiple_people_detected',
        'face_count',
        'issue_type'
    ]
    list_filter = ['multiple_people_detected', 'issue_type', 'timestamp']
    search_fields = ['interview__uuid', 'issue_type']
    readonly_fields = ['created_at', 'timestamp']
    ordering = ['-timestamp']
