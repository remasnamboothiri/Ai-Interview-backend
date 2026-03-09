# agents/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Agent
from .serializers import AgentSerializer
import logging

logger = logging.getLogger(__name__)

# Import DefaultQuestion from the correct app
try:
    from default_questions.models import DefaultQuestion
except ImportError:
    DefaultQuestion = None
    logger.warning("DefaultQuestion model not found — question save/load will be skipped")


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

    def _save_questions(self, agent, questions_data):
        """Helper: Save default questions for an agent (replace all existing)."""
        if DefaultQuestion is None:
            logger.warning("DefaultQuestion model not available, skipping question save")
            return

        # Delete existing questions for this agent
        DefaultQuestion.objects.filter(agent=agent).delete()

        # Create new questions
        saved_count = 0
        for q in questions_data:
            question_text = ''
            if isinstance(q, dict):
                question_text = q.get('question_text', '').strip()
            elif isinstance(q, str):
                question_text = q.strip()

            if question_text:
                DefaultQuestion.objects.create(
                    agent=agent,
                    question_text=question_text,
                )
                saved_count += 1

        logger.info(f"Saved {saved_count} questions for agent {agent.id} ({agent.name})")

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
        # Make a mutable copy of request data so we can pop default_questions
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        questions_data = data.pop('default_questions', [])

        serializer = AgentSerializer(data=data)
        if serializer.is_valid():
            agent = serializer.save()

            # Save questions if provided
            if questions_data:
                self._save_questions(agent, questions_data)

            return Response({
                'success': True,
                'data': AgentSerializer(agent).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """PUT /api/agents/{id}/ - Update agent"""
        try:
            agent = Agent.objects.get(pk=pk)

            # Make a mutable copy of request data so we can pop default_questions
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            questions_data = data.pop('default_questions', None)

            serializer = AgentSerializer(agent, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()

                # Update questions if provided (replace all existing)
                if questions_data is not None:
                    self._save_questions(agent, questions_data)

                return Response({
                    'success': True,
                    'data': AgentSerializer(agent).data
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



# from django.shortcuts import render

# # Create your views here.
# from rest_framework import viewsets, status
# from rest_framework.response import Response
# from .models import Agent
# from .serializers import AgentSerializer

# class AgentViewSet(viewsets.ModelViewSet):
#     queryset = Agent.objects.all()
#     serializer_class = AgentSerializer
    
#     def list(self, request):
#         """GET /api/agents/ - List all agents"""
#         agents = Agent.objects.all()
#         serializer = AgentSerializer(agents, many=True)
#         return Response({
#             'success': True,
#             'data': serializer.data
#         })
    
#     def retrieve(self, request, pk=None):
#         """GET /api/agents/{id}/ - Get single agent"""
#         try:
#             agent = Agent.objects.get(pk=pk)
#             serializer = AgentSerializer(agent)
#             return Response({
#                 'success': True,
#                 'data': serializer.data
#             })
#         except Agent.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Agent not found'
#             }, status=status.HTTP_404_NOT_FOUND)
    
#     def create(self, request):
#         """POST /api/agents/ - Create new agent"""
#         serializer = AgentSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({
#                 'success': True,
#                 'data': serializer.data
#             }, status=status.HTTP_201_CREATED)
#         return Response({
#             'success': False,
#             'errors': serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     def update(self, request, pk=None):
#         """PUT /api/agents/{id}/ - Update agent"""
#         try:
#             agent = Agent.objects.get(pk=pk)
#             serializer = AgentSerializer(agent, data=request.data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response({
#                     'success': True,
#                     'data': serializer.data
#                 })
#             return Response({
#                 'success': False,
#                 'errors': serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#         except Agent.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Agent not found'
#             }, status=status.HTTP_404_NOT_FOUND)
    
#     def destroy(self, request, pk=None):
#         """DELETE /api/agents/{id}/ - Delete agent"""
#         try:
#             agent = Agent.objects.get(pk=pk)
#             agent.delete()
#             return Response({
#                 'success': True,
#                 'message': 'Agent deleted successfully'
#             })
#         except Agent.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Agent not found'
#             }, status=status.HTTP_404_NOT_FOUND)
