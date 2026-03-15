from django.urls import path
from . import views

urlpatterns = [
    path('tts/', views.tts_synthesize, name='tts-synthesize'),
    path('stt-token/', views.stt_token, name='stt-token'),
    path('tts-voices/', views.tts_voices, name='tts-voices'),
]