from rest_framework import serializers
from .models import Interview
from jobs.serializers import JobSerializer
from candidates.serializers import CandidateSerializer
from agents.serializers import AgentSerializer
from users.serializers import UserSerializer

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
    job = JobSerializer(read_only=True)
    candidate = CandidateSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)
    recruiter = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    cancelled_by = UserSerializer(read_only=True)
    
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
        validated_data['created_by'] = self.context['request'].user
        validated_data['recruiter'] = self.context['request'].user
        return super().create(validated_data)

class InterviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'scheduled_at', 'duration_minutes', 'status', 'interview_type',
            'meeting_link', 'instructions', 'cancellation_reason'
        ]