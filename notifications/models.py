from django.db import models

# Create your models here.
from django.db import models
from users.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_cancelled', 'Interview Cancelled'),
        ('application_received', 'Application Received'),
        ('result_available', 'Result Available'),
        ('application_status_changed', 'Application Status Changed'),
        ('interview_reminder', 'Interview Reminder'),
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
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.email}"
