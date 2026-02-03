from django.db import models

# Create your models here.
from django.db import models
from interviews.models import Interview
from interview_data.models import InterviewData


class InterviewScreenshot(models.Model):
    """Stores proctoring screenshots captured during interviews"""
    
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='screenshots'
    )
    session = models.ForeignKey(
        InterviewData,
        on_delete=models.CASCADE,
        related_name='screenshots',
        null=True,
        blank=True
    )
    screenshot_url = models.URLField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    screenshot_number = models.IntegerField(default=1)
    
    # Proctoring detection
    multiple_people_detected = models.BooleanField(default=False)
    face_count = models.IntegerField(default=0)
    confidence_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True
    )
    issue_type = models.CharField(
        max_length=50,
        choices=[
            ('multiple_people', 'Multiple People'),
            ('no_face', 'No Face'),
            ('looking_away', 'Looking Away'),
            ('phone_detected', 'Phone Detected'),
        ],
        null=True,
        blank=True
    )
    
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'interview_screenshots'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['interview', 'timestamp']),
            models.Index(fields=['session']),
        ]
    
    def __str__(self):
        return f"Screenshot #{self.screenshot_number} - Interview {self.interview_id}"
