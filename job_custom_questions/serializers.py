from rest_framework import serializers
from .models import JobCustomQuestion

class JobCustomQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCustomQuestion
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
