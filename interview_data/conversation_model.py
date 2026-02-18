from django.db import models
from interviews.models import Interview

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
