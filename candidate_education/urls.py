from django.urls import path
from . import views

urlpatterns = [
    path('', views.education_list_create, name='education-list-create'),
    path('<int:pk>/', views.education_detail, name='education-detail'),
]
