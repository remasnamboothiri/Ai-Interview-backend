from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import InterviewResult

@admin.register(InterviewResult)
class InterviewResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'interview', 'overall_score', 'recommendation', 'result_generated_at']
    list_filter = ['recommendation', 'result_generated_at']
    search_fields = ['interview__uuid', 'recommendation']
    readonly_fields = ['result_generated_at', 'created_at', 'updated_at']
