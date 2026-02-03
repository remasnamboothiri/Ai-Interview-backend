from rest_framework import serializers
from .models import CandidateEducation

class CandidateEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateEducation
        fields = [
            'id',
            'candidate',
            'degree',
            'institution',
            'graduation_year',
            'is_current',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
