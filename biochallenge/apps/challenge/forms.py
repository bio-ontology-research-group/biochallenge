from django import forms
from challenge.models import Submission


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
        return self.instance
