from django.db import models

# Create your models here.
from django.db import models
from agents.models import Agent

class EvaluationCriteria(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='evaluation_criteria')
    criteria_name = models.CharField(max_length=255)
    weight_percentage = models.IntegerField()  # 0-100
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.criteria_name} ({self.weight_percentage}%)"
