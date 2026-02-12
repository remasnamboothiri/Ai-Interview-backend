from rest_framework import serializers
from .models import Interview
from jobs.models import Job
from candidates.models import Candidate
from agents.models import Agent
from users.models import User
from companies.models import Company

class NestedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']

class NestedCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name']

class NestedJobSerializer(serializers.ModelSerializer):
    company = NestedCompanySerializer(read_only=True)
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'company']

class NestedCandidateSerializer(serializers.ModelSerializer):
    user = NestedUserSerializer(read_only=True)
    
    class Meta:
        model = Candidate
        fields = ['id', 'user']

class NestedAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ['id', 'name']

class InterviewSerializer(serializers.ModelSerializer):
    # Read-only fields for display
    job_title = serializers.CharField(source='job.title', read_only=True)
    candidate_name = serializers.CharField(source='candidate.user.full_name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.user.email', read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    recruiter_name = serializers.CharField(source='recruiter.full_name', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id', 'uuid', 'job', 'candidate', 'recruiter', 'agent',
            'scheduled_at', 'duration_minutes', 'status', 'interview_type',
            'meeting_link', 'instructions', 'email_sent', 'email_sent_at',
            'candidate_notified', 'created_at', 'created_by', 'updated_at',
            'updated_by', 'cancelled_at', 'cancelled_by', 'cancellation_reason',
            'job_title', 'candidate_name', 'candidate_email', 'agent_name',
            'recruiter_name', 'company_name'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at', 'email_sent_at']

class InterviewDetailSerializer(serializers.ModelSerializer):
    job = NestedJobSerializer(read_only=True)
    candidate = NestedCandidateSerializer(read_only=True)
    agent = NestedAgentSerializer(read_only=True)
    recruiter = NestedUserSerializer(read_only=True)
    created_by = NestedUserSerializer(read_only=True)
    updated_by = NestedUserSerializer(read_only=True)
    cancelled_by = NestedUserSerializer(read_only=True)
    
    class Meta:
        model = Interview
        fields = '__all__'
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']

class InterviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'job', 'candidate', 'agent', 'scheduled_at', 'duration_minutes',
            'interview_type', 'meeting_link', 'instructions'
        ]
    
    def create(self, validated_data):
        # Get user from request context - handle case where user might be None
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            validated_data['recruiter'] = request.user
        else:
            # If user is not authenticated, set fields to None (allowed by model)
            validated_data['created_by'] = None
            validated_data['recruiter'] = None
        return super().create(validated_data)

class InterviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'scheduled_at', 'duration_minutes', 'status', 'interview_type',
            'meeting_link', 'instructions', 'cancellation_reason'
        ]
