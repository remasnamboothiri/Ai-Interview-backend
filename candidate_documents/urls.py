from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list_create, name='document-list-create'),
    path('<int:pk>/', views.document_detail, name='document-detail'),
]
