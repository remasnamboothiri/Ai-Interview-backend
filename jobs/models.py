from django.db import models

# Create your models here.
from django.db import models
from users.models import User
from companies.models import Company
from agents.models import Agent

class Job(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('lead', 'Lead/Principal'),
    ]
    
    WORK_MODE_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('on-site', 'On-site'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]

    # Basic Info
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPE_CHOICES)
    experience_level = models.CharField(max_length=50, choices=EXPERIENCE_LEVEL_CHOICES)
    work_mode = models.CharField(max_length=50, choices=WORK_MODE_CHOICES)
    application_deadline = models.DateField(null=True, blank=True)
    
    # Details
    skills_required = models.JSONField(default=list)  # ["React", "Node.js"]
    benefits = models.TextField(blank=True)
    salary_range = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    requirements = models.TextField()
    
    # Relationships
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs_created')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='jobs_authored')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='jobs_modified')
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    updated_ip = models.GenericIPAddressField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
