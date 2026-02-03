from rest_framework import serializers
from .models import JobApplication
from jobs.serializers import JobSerializer
from candidates.serializers import CandidateSerializer
from users.serializers import UserSerializer

class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    candidate_name = serializers.CharField(source='candidate.user.full_name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.user.email', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'candidate', 'applied_at', 'application_status',
            'created_by', 'created_at', 'updated_by', 'updated_at',
            'job_title', 'candidate_name', 'candidate_email', 'company_name', 'created_by_name'
        ]
        read_only_fields = ['id', 'applied_at', 'created_at', 'updated_at']

class JobApplicationDetailSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    candidate = CandidateSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'candidate', 'applied_at', 'application_status',
            'created_by', 'created_at', 'updated_by', 'updated_at'
        ]
        read_only_fields = ['id', 'applied_at', 'created_at', 'updated_at']

class JobApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['job', 'candidate', 'application_status']
        
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)