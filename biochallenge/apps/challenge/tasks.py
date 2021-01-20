from celery import shared_task
from subprocess import Popen, PIPE
from challenge.models import Challenge, Release, Submission
from django.utils import timezone
import requests
import datetime
import os
from django.apps import apps

from time import sleep
from scipy.stats import rankdata

from challenge.evaluation.parseAxioms import read_triplets_file
from challenge.evaluation.triplets import Triplet

def get_release_version(endpoint):
    try:
        r = requests.head(endpoint)
        version_string = r.headers['ETag']
        version = version_string[3:-1]
        return version
    except Exception as e:
        print(e)
    date = timezone.now()
    return f'{date.year}_{date.month:02d}'
        
@shared_task
def load_release(challenge_id):
    challenge = Challenge.objects.get(pk=challenge_id)
    version = get_release_version(challenge.sparql_endpoint)
    y, m = version.split('_')
    y, m = int(y), int(m)
    date = datetime.datetime(year=y, month=m, day=1)
    print('Release version', version)
    latest_release = challenge.get_latest_release()
    if latest_release is not None and latest_release.version == version:
        print('No new release')
        return
    
    release = Release(
        challenge=challenge,
        sparql_endpoint=challenge.sparql_endpoint,
        sparql_query=challenge.sparql_query,
        date=date,
        version=version)
    release.save()

    challenge.status = challenge.UPDATING
    challenge.save()
    
    # Load release data
    env = dict(os.environ)
    env['JAVA_OPTS'] = '-Xms2g -Xmx32g'
    p = Popen(['groovy', challenge.script, '-c', release.get_dir(),
               '-j', release.get_config_file(),], env=env)
    
    if p.wait() == 0:
        challenge.status = challenge.ACTIVE
    else:
        challenge.status = challenge.UPDATE_FAILED
    challenge.save()
        


@shared_task
def compute_hits_k(submission_id, gt_file, pred_file, k):

    #sleep(60)
    triplets_gt   = read_triplets_file(gt_file)
    triplets_pred = read_triplets_file(pred_file)

    rels = set([t.relation for t in triplets_gt] + [t.relation for t in triplets_pred])

    grouped_gt_rels   = Triplet.groupBy_relation(triplets_gt)       # {rel1: [triplets with rel1], rel2: [triplets with rel2], ...}
    grouped_pred_rels = Triplet.groupBy_relation(triplets_pred)


    hits = 0
    ranks = {}
    for rel in rels:
        if rel in grouped_gt_rels:
            gt = grouped_gt_rels[rel]
        else:
            gt = []
        preds = grouped_pred_rels[rel]

        scores = [x.score for x in preds]   
        ranking = rankdata(scores, method='average')

        for i in range(len(preds)):
            rank = ranking[i]            
            pred = preds[i]
         #   print(pred, ranking[i])
            if pred in gt and rank <= k:
                hits+=1
        
            if rank not in ranks:
                ranks[rank] = 0
            ranks[rank] += 1


    result = hits/len(triplets_gt)

    rank_auc = compute_rank_roc(ranks,1)

    
    submission = Submission.objects.get(pk=submission_id)
    submission.hits_10 = result
    submission.save()

    return result
