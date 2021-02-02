from django.urls import include, path
from django.contrib.auth.decorators import login_required
from accounts.views import (
    ProfileDetailView, ProfileUpdateView,
    TeamCreateView, TeamUpdateView, TeamListView,
    TeamMemberCreateView)


urlpatterns = [
    path('', include('allauth.urls')),
    path('profile/', login_required(
        ProfileDetailView.as_view()), name='profile'),
    path('profile/edit/', login_required(
        ProfileUpdateView.as_view()), name='profile_edit'),
    path('teams/', login_required(
        TeamListView.as_view()), name='team_list'),
    path('teams/create', login_required(
        TeamCreateView.as_view()), name='team_create'),
    path('teams/edit/<int:pk>', login_required(
        TeamUpdateView.as_view()), name='team_edit'),
    path('teams/invitemember/<int:team_pk>', login_required(
        TeamMemberCreateView.as_view()), name='team_member_invite'),

]
