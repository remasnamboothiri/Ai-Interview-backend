from django.db import models

# Create your models here.
from django.db import models
from jobs.models import Job

class JobCustomQuestion(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='custom_questions')
    question_text = models.TextField()
    is_mandatory = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.question_text[:50]
