from rest_framework import serializers
from .models import Recruiter

class RecruiterSerializer(serializers.ModelSerializer):
    # Optional: Add user and company details
    user = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    
    class Meta:
        model = Recruiter
        fields = [
            'id', 'user_id', 'company_id', 'role', 
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_ip', 'updated_ip', 'user', 'company'
        ]
    
    def get_user(self, obj):
        """Get user details from users table"""
        from users.models import User
        try:
            user = User.objects.get(id=obj.user_id)
            return {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'is_active': user.is_active
            }
        except User.DoesNotExist:
            return None
    
    def get_company(self, obj):
        """Get company details from companies table"""
        from companies.models import Company
        try:
            company = Company.objects.get(id=obj.company_id)
            return {
                'id': company.id,
                'name': company.name
            }
        except Company.DoesNotExist:
            return None
