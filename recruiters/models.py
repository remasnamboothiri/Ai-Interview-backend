from django.db import models

# Create your models here.
from django.db import models

class Recruiter(models.Model):
    # Links
    user_id = models.IntegerField(unique=True)  # One user can only be one recruiter
    company_id = models.IntegerField()
    
    # Role
    role = models.CharField(max_length=100, blank=True, null=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    created_ip = models.GenericIPAddressField(blank=True, null=True)
    updated_ip = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        db_table = 'recruiters'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recruiter {self.user_id} - Company {self.company_id}"
