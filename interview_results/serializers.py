from rest_framework import serializers
from .models import InterviewResult
from interviews.serializers import InterviewSerializer
from interview_data.serializers import InterviewDataSerializer

class InterviewResultSerializer(serializers.ModelSerializer):
    interview_detail = InterviewSerializer(source='interview', read_only=True)
    primary_session_detail = InterviewDataSerializer(source='primary_session', read_only=True)
    
    class Meta:
        model = InterviewResult
        fields = [
            'id', 'interview', 'interview_detail', 'primary_session', 'primary_session_detail',
            'overall_score', 'technical_score', 'communication_score', 'cultural_fit_score', 'behavioral_score',
            'questions_asked', 'response_times', 'behavioral_analysis', 'skill_assessment',
            'strengths', 'weaknesses', 'red_flags', 'recommendation',
            'transcript', 'recording_url', 'ai_feedback', 'recruiter_feedback',
            'interview_quality', 'technical_depth', 'result_document',
            'result_generated_at', 'result_reviewed_at', 'result_reviewed_by',
            'created_at', 'created_by', 'updated_at', 'updated_by'
        ]
        read_only_fields = ['id', 'result_generated_at', 'created_at', 'updated_at']

class InterviewResultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewResult
        fields = [
            'interview', 'primary_session', 'overall_score', 'technical_score', 
            'communication_score', 'cultural_fit_score', 'behavioral_score',
            'questions_asked', 'response_times', 'behavioral_analysis', 'skill_assessment',
            'strengths', 'weaknesses', 'red_flags', 'recommendation',
            'transcript', 'recording_url', 'ai_feedback', 'recruiter_feedback',
            'interview_quality', 'technical_depth', 'result_document'
        ]

class InterviewResultUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewResult
        fields = [
            'primary_session', 'overall_score', 'technical_score', 'communication_score',
            'cultural_fit_score', 'behavioral_score', 'questions_asked', 'response_times',
            'behavioral_analysis', 'skill_assessment', 'strengths', 'weaknesses', 'red_flags',
            'recommendation', 'transcript', 'recording_url', 'ai_feedback', 'recruiter_feedback',
            'interview_quality', 'technical_depth', 'result_document', 'result_reviewed_at',
            'result_reviewed_by'
        ]
