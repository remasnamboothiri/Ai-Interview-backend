from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Company
from .serializers import CompanySerializer

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def list(self, request):         #This function handles GET requests to /api/companies/
        companies = self.get_queryset()     # get all companies from datbase
        serializer = self.get_serializer(companies, many=True)  #Convert all companies to JSON forma
        return Response({
            'success': True,
            'count': companies.count(),
            'data': serializer.data
        })
    
    def create(self, request):  #This function handles POST requests to /api/companies/
        serializer = self.get_serializer(data=request.data)  #Take the JSON data from the request and prepare to convert it to a Company object
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Company created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
