from django.db import models

# Create your models here.
from django.db import models
from jobs.models import Job
from candidates.models import Candidate
from users.models import User
from agents.models import Agent
import uuid

class Interview(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    INTERVIEW_TYPE_CHOICES = [
        ('ai_only', 'AI Only'),
        ('human_only', 'Human Only'),
        ('hybrid', 'Hybrid'),
    ]
    
    # Primary Key
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Foreign Keys
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='interviews')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews')
    #recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_interviews')
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_interviews', null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='interviews')
    
    # Schedule Information
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Interview Details
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPE_CHOICES, default='ai_only')
    meeting_link = models.URLField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    
    # Email Notifications
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(blank=True, null=True)
    candidate_notified = models.BooleanField(default=False)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    #created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_interviews')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_interviews', null=True, blank=True)

    created_ip = models.GenericIPAddressField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_interviews', null=True, blank=True)
    updated_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Cancellation
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_interviews')
    cancellation_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'interviews'
        ordering = ['-scheduled_at']
    
    def __str__(self):
        return f"Interview: {self.candidate.user.full_name} for {self.job.title}"