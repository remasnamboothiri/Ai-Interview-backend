from rest_framework import serializers
from .models import Candidate
from users.models import User

class CandidateSerializer(serializers.ModelSerializer):
    # Read-only fields from related User model
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = Candidate
        fields = [
            'id',
            'user',  # Django will automatically accept 'user_id' in POST requests
            'full_name',
            'email',
            'phone',
            'experience_years',
            'current_company',
            'linkedin_url',
            'portfolio_url',
            'skills',
            'general_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'email', 'phone']




# from rest_framework import serializers
# from .models import Candidate

# class CandidateSerializer(serializers.ModelSerializer):
#     # Read-only fields from related User model
#     full_name = serializers.CharField(source='user.full_name', read_only=True)
#     email = serializers.EmailField(source='user.email', read_only=True)
#     phone = serializers.CharField(source='user.phone', read_only=True)
    
#     # Explicitly define user_id as writable
#     #user_id = serializers.IntegerField(write_only=False, required=True)
#     # ✅ CHANGE THIS LINE
#     user = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.all(),
#         write_only=False,
#         required=True
#     )
#     class Meta:
#         model = Candidate
#         fields = [
#             'id',
#             'user',
#             'full_name',
#             'email',
#             'phone',
#             'experience_years',
#             'current_company',
#             'linkedin_url',
#             'portfolio_url',
#             'skills',
#             'general_notes',
#             'created_at',
#             'updated_at',
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'email', 'phone']
    
    def create(self, validated_data):
        """
        Create and return a new Candidate instance
        """
        return Candidate.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing Candidate instance
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
