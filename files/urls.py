from django.urls import path
from . import views

urlpatterns = [
    path('', views.file_list_create, name='file-list-create'),
    path('<int:pk>/', views.file_detail, name='file-detail'),
]
