from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import DefaultQuestion
from .serializers import DefaultQuestionSerializer

class DefaultQuestionViewSet(viewsets.ModelViewSet):
    queryset = DefaultQuestion.objects.all()
    serializer_class = DefaultQuestionSerializer
