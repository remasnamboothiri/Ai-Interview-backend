from django.db import models

# Create your models here.
from django.db import models
from candidates.models import Candidate

class CandidateEducation(models.Model):
    """
    CANDIDATE_EDUCATION TABLE
    Stores education history for candidates
    """
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='education_records'
    )
    degree = models.CharField(max_length=255)
    institution = models.CharField(max_length=255)
    graduation_year = models.IntegerField()
    is_current = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidate_education'
        ordering = ['-graduation_year']

    def __str__(self):
        return f"{self.candidate.user.full_name} - {self.degree}"
