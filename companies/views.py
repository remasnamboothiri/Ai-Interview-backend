from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Company
from .serializers import CompanySerializer
from activity_logs.models import ActivityLog


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def list(self, request):
        """Get all companies"""
        companies = self.get_queryset()
        serializer = self.get_serializer(companies, many=True)
        return Response({
            'success': True,
            'count': companies.count(),
            'data': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """Get single company by ID"""
        try:
            company = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(company)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        """Create new company"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save()
            # ✅ ADD THIS: Create activity log
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='company_created',
                resource_type='Company',
                resource_id=company.id,
                details={'company_name': company.name},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({
                'success': True,
                'message': 'Company created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Update existing company"""
        try:
            company = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(company, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                # ✅ ADD THIS: Create activity log
                ActivityLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='company_updated',
                    resource_type='Company',
                    resource_id=company.id,
                    details={'company_name': company.name},
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                return Response({
                    'success': True,
                    'message': 'Company updated successfully',
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """Delete company"""
        try:
            company = self.get_queryset().get(pk=pk)
            company_name = company.name
            company_id = company.id 
            company.delete()
            
            # ✅ ADD THIS: Create activity log
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='company_deleted',
                resource_type='Company',
                resource_id=company_id,
                details={'company_name': company_name},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({
                'success': True,
                'message': 'Company deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)
