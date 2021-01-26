"""biochallenge API URL Configuration
"""
from django.urls import include, path
from django.conf import settings
from django.contrib.auth.decorators import login_required
from challenge import views

urlpatterns = [
    path('', views.ChallengeListView.as_view(), name='challenges'),
    path('view/<int:pk>',
         views.ChallengeDetailView.as_view(), name='challenge_view'),
    path('submissions', login_required(
        views.SubmissionListView.as_view()), name='submissions'),
    path('challenge_submissions/<int:release_pk>', 
        views.ChallengeSubmissionListView.as_view(), name='challenge_submissions'),
    path('submit/<int:release_pk>', login_required(
        views.SubmissionCreateView.as_view()), name='challenge_submit'),
]
