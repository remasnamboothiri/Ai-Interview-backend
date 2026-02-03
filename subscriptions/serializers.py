from rest_framework import serializers
from .models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id', 'company_id', 'plan_name', 'plan_price', 'billing_cycle',
            'max_recruiters', 'max_jobs', 'max_interviews_per_month', 
            'max_storage_gb', 'features', 'status', 'trial_ends_at',
            'current_period_start', 'current_period_end', 'cancel_at_period_end',
            'payment_method', 'last_payment_date', 'next_payment_date', 
            'payment_status', 'created_at', 'updated_at', 'cancelled_at', 
            'cancelled_by'
        ]
