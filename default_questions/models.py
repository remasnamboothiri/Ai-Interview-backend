from django.db import models

# Create your models here.
from django.db import models
from agents.models import Agent

class DefaultQuestion(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='default_questions')
    question_text = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.question_text[:50]
