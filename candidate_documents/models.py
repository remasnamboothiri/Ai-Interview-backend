from django.db import models

# Create your models here.
from django.db import models
from candidates.models import Candidate
from files.models import File

class CandidateDocument(models.Model):
    """
    CANDIDATE_DOCUMENTS TABLE
    Links files to candidates
    """
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name='candidate_documents'
    )
    document_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    is_primary = models.BooleanField(default=False)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'candidate_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.candidate.user.full_name} - {self.file_name}"
