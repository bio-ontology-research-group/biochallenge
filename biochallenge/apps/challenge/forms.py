from django import forms
from challenge.models import Submission
from challenge.tasks import compute_hits_k
import os

class SubmissionForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ['predictions_file',]

    def __init__(self, *args, **kwargs):
        self.release = kwargs.pop('release')
        self.request = kwargs.pop('request')
        super(SubmissionForm, self).__init__(*args, **kwargs)


    def save(self, *args, **kwargs):
        self.instance = super(SubmissionForm, self).save(commit=False)
        self.instance.release = self.release
        self.instance.user = self.request.user
        self.instance.save()
        filename = self.instance.predictions_file.path
        ground_truth_file = os.getcwd() + '/biochallenge/apps/challenge/evaluation/example_gt.tsv'
        compute_hits_k.delay(self.instance.id, ground_truth_file, filename, 10)
        return self.instance
