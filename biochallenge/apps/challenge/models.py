from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.conf import settings
import os
import json
import datetime
from time import sleep
from celery import shared_task
from challenge.evaluation.parseAxioms import read_triplets_file
from challenge.evaluation.triplets import Triplet
from scipy.stats import rankdata
from accounts.models import Team


class Challenge(models.Model):
    DRAFT = 'draft'
    ACTIVE = 'active'
    UPDATING = 'updating'
    UPDATE_FAILED = 'update_failed'
    WITHDRAWN = 'withdrawn'
    STATUSES = (
        (DRAFT, DRAFT),
        (ACTIVE, ACTIVE),
        (UPDATING, UPDATING),
        (UPDATE_FAILED, UPDATE_FAILED),
        (WITHDRAWN, WITHDRAWN))

    DEFAULT = 'updater/Challenge.groovy'
    PARALLEL = 'updater/ChallengeUniprot.groovy'
    SCRIPTS = ((DEFAULT, DEFAULT), (DEFAULT, PARALLEL))
    name = models.CharField(max_length=127)
    status = models.CharField(max_length=15, choices=STATUSES)
    description = models.TextField()
    download_link = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='challenges/', null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)
    sparql_endpoint = models.CharField(max_length=255)
    sparql_query = models.TextField()
    script = models.CharField(max_length=31, default=DEFAULT, choices=SCRIPTS)

    def __str__(self):
        return self.name

    def get_latest_release(self):
        return self.releases.order_by('-pk').first()

    @property
    def release(self):
        return self.get_latest_release()


class Release(models.Model):
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name='releases')
    sparql_endpoint = models.CharField(max_length=255)
    sparql_query = models.TextField()
    date = models.DateTimeField()
    version = models.CharField(max_length=31)

    def get_dir(self):
        rel_dir = os.path.join(
            settings.MEDIA_ROOT,
            f'{self.challenge.id:06d}',
            f'{self.version}')
        return rel_dir

    def get_config_file(self):
        return os.path.join(self.get_dir(), 'config.json')

    def get_data_url(self):
        return '/' + os.path.join(self.get_dir(), 'data.csv.gz')


def submission_dir_path(instance, filename):
    return f'submissions/{instance.team.id:06d}/{instance.release.id:06d}/{filename}'

class Submission(models.Model):
    EVALUATION = 'evaluation'
    ACTIVE = 'active'
    WITHDRAWN = 'withdrawn'
    ERROR = 'error'
    STATUSES = (
        (EVALUATION, EVALUATION),
        (ACTIVE, ACTIVE),
        (WITHDRAWN, WITHDRAWN),
        (ERROR, ERROR))
    
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True,
        related_name='submissions')
    release = models.ForeignKey(
        Release, on_delete=models.SET_NULL, null=True,
        related_name='submissions')
    date = models.DateTimeField(default=timezone.now)
    predictions_file = models.FileField(upload_to=submission_dir_path)
    status = models.CharField(max_length=31, default=EVALUATION)
    hits_10 = models.FloatField(null=True)
    auc = models.FloatField(null=True)
    
