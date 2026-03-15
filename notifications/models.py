from django.db import models
from users.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        # Interviews
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_started', 'Interview Started'),
        ('interview_completed', 'Interview Completed'),
        ('interview_cancelled', 'Interview Cancelled'),
        ('interview_reminder', 'Interview Reminder'),
        # Results
        ('result_available', 'Result Available'),
        # Jobs
        ('job_created', 'Job Created'),
        ('job_updated', 'Job Updated'),
        # Candidates
        ('candidate_registered', 'Candidate Registered'),
        ('candidate_added', 'Candidate Added'),
        # Applications
        ('application_received', 'Application Received'),
        ('application_status_changed', 'Application Status Changed'),
        # AI Agents
        ('agent_created', 'Agent Created'),
        # System
        ('system_announcement', 'System Announcement'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_resource_type = models.CharField(max_length=50, blank=True, null=True)
    related_resource_id = models.IntegerField(blank=True, null=True)
    action_url = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.user.email}"