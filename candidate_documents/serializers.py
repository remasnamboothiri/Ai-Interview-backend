from rest_framework import serializers
from .models import CandidateDocument

class CandidateDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateDocument
        fields = [
            'id',
            'candidate',
            'file',
            'document_url',
            'file_name',
            'file_size',
            'is_primary',
            'uploaded_at',
            'created_at',
        ]
        read_only_fields = ['id', 'uploaded_at', 'created_at']
