from django.db import models

# Create your models here.
from django.db import models

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('trial', 'Trial'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('overdue', 'Overdue'),
    ]
    
    # Link to company
    company_id = models.IntegerField(unique=True)  # One subscription per company
    
    # Plan Details
    plan_name = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    plan_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    
    # Plan Limits
    max_recruiters = models.IntegerField(default=1)  # -1 means unlimited
    max_jobs = models.IntegerField(default=5)  # -1 means unlimited
    max_interviews_per_month = models.IntegerField(default=10)
    max_storage_gb = models.IntegerField(default=1)
    features = models.JSONField(default=dict)  # {"ai_interviews": true, "video_recording": false}
    
    # Subscription Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    trial_ends_at = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateField(blank=True, null=True)
    current_period_end = models.DateField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    # Payment
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    last_payment_date = models.DateField(blank=True, null=True)
    next_payment_date = models.DateField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancelled_by = models.IntegerField(blank=True, null=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.plan_name} - Company {self.company_id}"
