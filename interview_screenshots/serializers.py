from rest_framework import serializers
from .models import InterviewScreenshot


class InterviewScreenshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewScreenshot
        fields = [
            'id',
            'interview',
            'session',
            'screenshot_url',
            'timestamp',
            'screenshot_number',
            'multiple_people_detected',
            'face_count',
            'confidence_score',
            'issue_type',
            'metadata',
            'created_at',
            'created_ip'
        ]
        read_only_fields = ['id', 'created_at', 'timestamp']


class InterviewScreenshotCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewScreenshot
        fields = [
            'interview',
            'session',
            'screenshot_url',
            'screenshot_number',
            'multiple_people_detected',
            'face_count',
            'confidence_score',
            'issue_type',
            'metadata',
            'created_ip'
        ]
