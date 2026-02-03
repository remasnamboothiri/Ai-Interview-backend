from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Subscription
from .serializers import SubscriptionSerializer

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    
    def list(self, request):
        """Get all subscriptions"""
        subscriptions = self.get_queryset()
        serializer = self.get_serializer(subscriptions, many=True)
        return Response({
            'success': True,
            'count': subscriptions.count(),
            'data': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """Get single subscription by ID"""
        try:
            subscription = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(subscription)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Subscription not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='company/(?P<company_id>[^/.]+)')
    def by_company(self, request, company_id=None):
        """Get subscription by company ID"""
        try:
            subscription = self.get_queryset().get(company_id=company_id)
            serializer = self.get_serializer(subscription)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Subscription not found for this company'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        """Create new subscription"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Subscription created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Update existing subscription"""
        try:
            subscription = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(subscription, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Subscription updated successfully',
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Subscription not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """Delete subscription"""
        try:
            subscription = self.get_queryset().get(pk=pk)
            subscription.delete()
            return Response({
                'success': True,
                'message': 'Subscription deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Subscription not found'
            }, status=status.HTTP_404_NOT_FOUND)
