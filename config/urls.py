"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from notifications import urls as notification_urls
from activity_logs import urls as activity_log_urls
from system_settings import urls as system_setting_urls

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/companies/', include('companies.urls')), 
    path('api/', include('users.urls')),      # User app urls
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/recruiters/', include('recruiters.urls')), 
    path('api/candidates/', include('candidates.urls')),
    path('api/candidate-education/', include('candidate_education.urls')),  
    path('api/files/', include('files.urls')),  
    path('api/candidate-documents/', include('candidate_documents.urls')),
    
    path('api/', include('agents.urls')),
    path('api/', include('evaluation_criteria.urls')),
    path('api/', include('default_questions.urls')),  
    
    path('api/', include('jobs.urls')),
    
    path('api/', include('job_custom_questions.urls')),
    path('api/', include('job_applications.urls')),
    
    path('api/', include('interviews.urls')),
    path('api/interview-data/', include('interview_data.urls')),
    path('api/interview-screenshots/', include('interview_screenshots.urls')),
    path('api/interview-results/', include('interview_results.urls')), 
    
    path('api/', include(notification_urls)),
    path('api/', include(activity_log_urls)), 
    
    path('api/', include(system_setting_urls)), 
]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
