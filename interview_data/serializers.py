from rest_framework import serializers
from .models import InterviewData

class InterviewDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewData
        fields = '__all__'
        read_only_fields = ['id', 'session_uuid', 'created_at', 'updated_at']

class InterviewDataCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewData
        fields = [
            'interview', 'session_number', 'candidate_ip', 
            'device_info', 'candidate_location'
        ]

class InterviewDataUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewData
        fields = [
            'url_opened_at', 'started_at', 'ended_at', 'actual_duration_minutes',
            'status', 'network_interruptions', 'questions_answered',
            'last_activity_at', 'completion_percentage', 'session_quality_score',
            'audio_quality', 'video_quality', 'is_primary_session'
        ]
