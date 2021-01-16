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
    post_save.disconnect(evaluate_submission, sender = Submission)
    filename = instance.predictions_file.path
    ground_truth_file = os.getcwd() + '/biochallenge/apps/challenge/evaluation/example_gt.tsv'
    
    compute_hits_10.delay(instance.id, ground_truth_file, filename, 10)
    #result = compute_hits_10.delay(ground_truth_file, filename, 10)
    #print(result.status, result.backend, result.get())
    #instance.hits_10 = result.get()
    #instance.save()

post_save.connect(evaluate_submission, sender = Submission)


@shared_task
def compute_hits_10(sumbission_id, gt_file, pred_file, k):

    sleep(60)
    triplets_gt   = read_triplets_file(gt_file)
    triplets_pred = read_triplets_file(pred_file)

    rels = set([t.relation for t in triplets_gt] + [t.relation for t in triplets_pred])

    grouped_gt_rels   = Triplet.groupBy_relation(triplets_gt)       # {rel1: [triplets with rel1], rel2: [triplets with rel2], ...}
    grouped_pred_rels = Triplet.groupBy_relation(triplets_pred)


    hits = 0
    for rel in rels:
        if rel in grouped_gt_rels:
            gt = grouped_gt_rels[rel]
        else:
            gt = []
        preds = grouped_pred_rels[rel]

        scores = [x.score for x in preds]
        ranking = rankdata(scores, method='average')

        for i in range(len(preds)):
            
            pred = preds[i]
         #   print(pred, ranking[i])
            if pred in gt and ranking[i] <= k:
                hits+=1
        
    result = hits/len(triplets_gt)
    
    submission = Submission.objects.get(pk=sumbission_id)
    submission.hits_10 = result
    submission.save()

    
    #return result