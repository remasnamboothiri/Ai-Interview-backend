from django.db import models

# Create your models here.
from django.db import models
from users.models import User
from companies.models import Company

class Agent(models.Model):
    INTERVIEW_TYPE_CHOICES = [
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('product', 'Product'),
        ('design', 'Design'),
        ('general', 'General'),
    ]
    
    AGENT_TYPE_CHOICES = [
        ('global', 'Global'),
        ('private', 'Private'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    # Basic Info
    name = models.CharField(max_length=255)
    interview_type = models.CharField(max_length=50, choices=INTERVIEW_TYPE_CHOICES)
    description = models.TextField()
    system_prompt = models.TextField()
    
    # Voice & Language
    language = models.CharField(max_length=50, default='english')
    voice_settings = models.CharField(max_length=100, default='professional-male')
    
    # Agent Type (NEW REQUIREMENT!)
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPE_CHOICES, default='private')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    # If agent_type='global', company=NULL
    # If agent_type='private', company=<specific company>
    
    # Model Parameters
    ai_model = models.CharField(max_length=100, default='gpt-4')
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2000)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='agents_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='agents_updated')
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    updated_ip = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return self.name
