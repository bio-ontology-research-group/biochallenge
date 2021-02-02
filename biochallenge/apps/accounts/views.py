from django.shortcuts import render
from django.urls import reverse
from django.views.generic import (
    DetailView, UpdateView, CreateView, ListView)
from django.contrib.auth.models import User
from accounts.forms import UserProfileForm, TeamForm, TeamMemberInviteForm
from accounts.models import UserProfile, Team, Member
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


class TeamMemberCreateView(CreateView):

    form_class = TeamMemberInviteForm
    model = Member
    template_name = 'account/team/invite_member.html'

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(TeamMemberCreateView, self).get_form_kwargs(
            *args, **kwargs)
        team_pk = self.kwargs.get('team_pk')
        try:
            team = Team.objects.get(pk=team_pk)
        except Team.DoesNotExist:
            raise Http404
        kwargs['team'] = team
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(TeamMemberCreateView, self).get_context_data(*args, **kwargs)
        context['team_pk'] = self.kwargs.get('team_pk')
        return context
    
    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse('team_edit', kwargs={'pk': self.object.team.pk})


class TeamUpdateView(FormRequestMixin, UpdateView):

    form_class = TeamForm
    model = Team
    template_name = 'account/team/edit.html'


    def get_context_data(self, *args, **kwargs):
        context = super(TeamUpdateView, self).get_context_data(*args, **kwargs)
        invite_form = TeamMemberInviteForm(team=self.get_object())
        context['invite_form'] = invite_form
        return context
    
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

