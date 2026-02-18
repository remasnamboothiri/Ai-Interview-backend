from django.db import models

# Create your models here.
from django.db import models
from interviews.models import Interview
import uuid

class InterviewData(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    # Primary Key
    id = models.AutoField(primary_key=True)
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.IntegerField(default=1)
    session_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Session Timing
    url_opened_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    actual_duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Session Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    candidate_ip = models.GenericIPAddressField(null=True, blank=True)
    candidate_location = models.CharField(max_length=255, null=True, blank=True)
    device_info = models.TextField(null=True, blank=True)
    
    # Session Quality
    is_primary_session = models.BooleanField(default=False)
    network_interruptions = models.IntegerField(default=0)
    questions_answered = models.IntegerField(default=0)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    completion_percentage = models.IntegerField(default=0)
    
    # Quality Scores
    session_quality_score = models.IntegerField(null=True, blank=True)
    audio_quality = models.IntegerField(null=True, blank=True)
    video_quality = models.IntegerField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'interview_data'
        ordering = ['-created_at']
        unique_together = ['interview', 'session_number']
    
    def __str__(self):
        return f"Session {self.session_number} for Interview {self.interview.id}"


class InterviewConversation(models.Model):
    """
    Stores conversation messages between AI and candidate during interview
    """
    SPEAKER_CHOICES = [
        ('ai', 'AI Interviewer'),
        ('candidate', 'Candidate'),
    ]
    
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='conversations')
    speaker = models.CharField(max_length=20, choices=SPEAKER_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'interview_conversations'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.speaker}: {self.message[:50]}..."
