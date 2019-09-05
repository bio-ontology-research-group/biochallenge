"""biochallenge API URL Configuration
"""
from django.urls import include, path
from django.conf import settings

urlpatterns = [
    path('challenge/', include('challenge.api_urls')),
]
