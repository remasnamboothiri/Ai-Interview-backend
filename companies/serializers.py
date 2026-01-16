from rest_framework import serializers
from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'industry', 'size', 'status', 'website', 
                  'description', 'email', 'phone', 'street_address', 
                  'city', 'state', 'country', 'postal_code',
                  'created_at', 'updated_at']
