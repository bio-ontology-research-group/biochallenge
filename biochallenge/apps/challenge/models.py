from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.conf import settings
import os
import json
import datetime
from challenge.evaluation.hits_k import compute_hits_10

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
            f'{self.id:06d}')
        return rel_dir

    def get_config_file(self):
        return os.path.join(self.get_dir(), 'config.json')

    def get_data_url(self):
        return '/' + os.path.join(self.get_dir(), 'data.tsv.gz')


def create_release_files(sender, instance, created, **kwargs):
    os.makedirs(instance.get_dir(), exist_ok=True)
    config_file = instance.get_config_file()
    f = open(config_file, 'w')
    data = {
        'endpoint': instance.sparql_endpoint,
        'query': instance.sparql_query,
        'dir': instance.get_dir()}
    data_json = json.dumps(data)
    f.write(data_json)
    f.close()

post_save.connect(create_release_files, sender=Release)


def submission_dir_path(instance, filename):
    return f'submissions/{instance.user.id:06d}/{instance.release.id:06d}/{filename}'

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
    
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='submissions')
    release = models.ForeignKey(
        Release, on_delete=models.SET_NULL, null=True,
        related_name='submissions')
    date = models.DateTimeField(default=timezone.now)
    predictions_file = models.FileField(upload_to=submission_dir_path)
    status = models.CharField(max_length=31, default=EVALUATION)
    hits_10 = models.FloatField(null=True)


def evaluate_submission(sender, instance, **kwargs):
    
    filename = instance.predictions_file
    ground_truth_file = 'challenge/evaluation/example_gt.tsv'

    hits_10 = compute_hits_10(ground_truth_file, filename, 10)
    instance.hits_10 = hits_10
    instance.save()

post_save.connect(evaluate_submission, sender = Submission)
