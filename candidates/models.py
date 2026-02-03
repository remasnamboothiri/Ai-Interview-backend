from django.db import models

# Create your models here.
from django.db import models
from users.models import User

class Candidate(models.Model):
    """
    CANDIDATES TABLE
    Stores detailed profiles for job seekers
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='candidate_profile'
    )
    experience_years = models.IntegerField(null=True, blank=True)
    current_company = models.CharField(max_length=255, null=True, blank=True)
    linkedin_url = models.URLField(max_length=500, null=True, blank=True)
    portfolio_url = models.URLField(max_length=500, null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
    general_notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='updated_candidates'
    )
    updated_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'candidates'
        ordering = ['-created_at']

    def __str__(self):
        return f"Candidate: {self.user.full_name}"
