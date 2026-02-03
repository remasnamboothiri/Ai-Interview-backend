from rest_framework import serializers
from .models import DefaultQuestion

class DefaultQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefaultQuestion
        fields = '__all__'
