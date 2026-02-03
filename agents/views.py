from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Agent
from .serializers import AgentSerializer

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    
    def list(self, request):
        """GET /api/agents/ - List all agents"""
        agents = Agent.objects.all()
        serializer = AgentSerializer(agents, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """GET /api/agents/{id}/ - Get single agent"""
        try:
            agent = Agent.objects.get(pk=pk)
            serializer = AgentSerializer(agent)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Agent.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Agent not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        """POST /api/agents/ - Create new agent"""
        serializer = AgentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """PUT /api/agents/{id}/ - Update agent"""
        try:
            agent = Agent.objects.get(pk=pk)
            serializer = AgentSerializer(agent, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Agent.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Agent not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """DELETE /api/agents/{id}/ - Delete agent"""
        try:
            agent = Agent.objects.get(pk=pk)
            agent.delete()
            return Response({
                'success': True,
                'message': 'Agent deleted successfully'
            })
        except Agent.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Agent not found'
            }, status=status.HTTP_404_NOT_FOUND)
