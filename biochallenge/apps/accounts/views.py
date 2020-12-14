from django.shortcuts import render
from django.urls import reverse
from django.views.generic import (
    DetailView, UpdateView, CreateView, ListView)
from django.contrib.auth.models import User
from accounts.forms import UserProfileForm, TeamForm
from accounts.models import UserProfile, Team
from biochallenge.mixins import FormRequestMixin
from django.db.models import Q
    
class ProfileDetailView(DetailView):
    model = User
    template_name = 'account/profile/view.html'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            return self.request.user
        return super(ProfileDetailView, self).get_object(queryset)



class ProfileUpdateView(UpdateView):

    form_class = UserProfileForm
    model = UserProfile
    template_name = 'account/profile/edit.html'

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_success_url(self, *args, **kwargs):
        return reverse('profile')


class TeamCreateView(FormRequestMixin, CreateView):

    form_class = TeamForm
    model = Team
    template_name = 'account/team/create.html'


    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse('team_edit', kwargs={'pk': self.object.pk})

class TeamUpdateView(FormRequestMixin, UpdateView):

    form_class = TeamForm
    model = Team
    template_name = 'account/team/edit.html'

    def get_success_url(self):
        return reverse('team_edit', kwargs={'pk': self.object.pk})


class TeamListView(ListView):
    model = Team
    template_name = 'account/team/list.html'

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        queryset = super(TeamListView, self).get_queryset(*args, **kwargs)
        queryset = queryset.filter(members=user)
        return queryset

