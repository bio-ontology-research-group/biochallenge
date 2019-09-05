from django.urls import reverse
from django.views import generic as views
from django.contrib.auth.models import User
from challenge.models import (
    Challenge, Submission)
from challenge.forms import (
    SubmissionForm)
from challenge.mixins import ReleaseMixin
from biochallenge.mixins import FormRequestMixin

    
class ChallengeListView(views.ListView):
    model = Challenge
    template_name = 'challenge/list.html'

    def get_queryset(self, *args, **kwargs):
        queryset = super(ChallengeListView, self).get_queryset(
            *args, **kwargs)
        return queryset.filter(status=Challenge.ACTIVE)

    
class ChallengeDetailView(views.DetailView):
    model = Challenge
    template_name = 'challenge/view.html'


class SubmissionCreateView(ReleaseMixin, FormRequestMixin, views.CreateView):
    model = Submission
    template_name = 'challenge/submit.html'
    form_class = SubmissionForm

    def get_success_url(self, *args, **kwargs):
        return reverse('submissions')


class SubmissionListView(views.ListView):
    model = Submission
    template_name = 'challenge/my_submissions.html'

    def get_queryset(self, *args, **kwargs):
        queryset = super(SubmissionListView, self).get_queryset(
            *args, **kwargs)
        return queryset.filter(user=self.request.user)
