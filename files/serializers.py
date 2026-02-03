from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'id',
            'user',
            'original_name',
            'stored_name',
            'file_path',
            'file_size',
            'mime_type',
            'file_type',
            'is_public',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'stored_name', 'file_path']
