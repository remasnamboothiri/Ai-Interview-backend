from django.urls import path
from . import views

urlpatterns = [
    path('', views.candidate_list_create, name='candidate-list-create'),
    path('<int:pk>/', views.candidate_detail, name='candidate-detail'),
]
