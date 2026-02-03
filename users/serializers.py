from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    company_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone', 'user_type', 'company_id', 
            'company_name', 'is_active', 'is_email_verified', 
            'avatar_url', 'timezone', 'created_at', 'updated_at', 
            'last_login_at', 'password'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login_at']
        
        
    def get_company_name(self, obj):  
        """
        Get company name from company_id
        """
        if obj.company_id:
            try:
                from companies.models import Company
                company = Company.objects.get(id=obj.company_id)
                return company.name
            except Company.DoesNotExist:
                return None
        return None
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        
        if password:
            user.password_hash = make_password(password)
        else:
            user.password_hash = make_password('DefaultPassword123!')
        
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.password_hash = make_password(password)
        
        instance.save()
        return instance
