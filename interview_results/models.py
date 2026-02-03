from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from interviews.models import Interview
from interview_data.models import InterviewData
from files.models import File
from users.models import User

class InterviewResult(models.Model):
    RECOMMENDATION_CHOICES = [
        ('hire', 'Hire'),
        ('reject', 'Reject'),
        ('maybe', 'Maybe'),
        ('second_round', 'Second Round'),
    ]

    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='result')
    primary_session = models.ForeignKey(InterviewData, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_result')
    
    overall_score = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(10)])
    technical_score = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(10)])
    communication_score = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(10)])
    cultural_fit_score = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(10)])
    behavioral_score = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    
    questions_asked = models.JSONField(default=list, blank=True)
    response_times = models.JSONField(default=list, blank=True)
    behavioral_analysis = models.JSONField(default=dict, blank=True)
    skill_assessment = models.JSONField(default=dict, blank=True)
    
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    red_flags = models.JSONField(default=list, blank=True)
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES)
    
    transcript = models.TextField(blank=True)
    recording_url = models.URLField(max_length=500, blank=True)
    ai_feedback = models.JSONField(default=dict, blank=True)
    recruiter_feedback = models.TextField(blank=True)
    
    interview_quality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True)
    technical_depth = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True)
    
    result_document = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='interview_results')
    
    result_generated_at = models.DateTimeField(auto_now_add=True)
    result_reviewed_at = models.DateTimeField(null=True, blank=True)
    result_reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_results')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_results')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_results')

    class Meta:
        db_table = 'interview_results'
        ordering = ['-created_at']

    def __str__(self):
        return f"Result for Interview {self.interview.id} - Score: {self.overall_score}"
