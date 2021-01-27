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
import numpy as np
from challenge.evaluation.parseAxioms import read_triplets_file
from challenge.evaluation.triplets import Triplet
import json

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


def create_release_files(release):
    os.makedirs(release.get_dir(), exist_ok=True)
    config_file = release.get_config_file()
    with open(config_file, 'w') as f:
        data = {
            'endpoint': release.sparql_endpoint,
            'query': release.sparql_query,
            'dir': release.get_dir()}
        data_json = json.dumps(data)
        f.write(data_json)

        
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

    create_release_files(release)

    # Load release data
    env = dict(os.environ)
    env['JAVA_OPTS'] = '-Xms1g -Xmx32g'
    p = Popen(['groovy', challenge.script, '-c', release.get_dir(),
               '-j', release.get_config_file(),], env=env)
    
    if p.wait() == 0:
        release.save()    



def compute_rank_roc(ranks, n_entities):

    auc_x = list(ranks.keys())
    auc_x.sort()
    auc_y = []
    tpr = 0
    sum_rank = sum(ranks.values())
    for x in auc_x:
        tpr += ranks[x]
        auc_y.append(tpr / sum_rank)
    auc_x.append(n_entities)
    auc_y.append(1)
    auc = np.trapz(auc_y, auc_x) 
    return auc/n_entities

@shared_task
def compute_metrics(submission_id, gt_file, pred_file, k):

    #Computes hits@k and AUC


    #sleep(60)
    triplets_gt   = read_triplets_file(gt_file)
    triplets_pred = read_triplets_file(pred_file)

    entities = set([t.entity_1 for t in triplets_gt] + [t.entity_2 for t in triplets_gt])

    grouped_gt   = Triplet.groupBy_entity_relation(triplets_gt)       # {rel1: [triplets with rel1], rel2: [triplets with rel2], ...}
    grouped_pred = Triplet.groupBy_entity_relation(triplets_pred)

    
    keys = set(list(grouped_gt.keys()) + list(grouped_pred.keys()))

    hits = 0
    ranks = {}
    for key in keys:
        if key in grouped_gt:
            gt = grouped_gt[key]
        else:
            gt = []
        preds = grouped_pred[key]

        scores = [-x.score for x in preds]   
        ranking = rankdata(scores, method='average')

        for i in range(len(ranking)):
            rank = ranking[i]            
            pred = preds[i]
        
            if pred in gt and rank <= k:
                hits+=1
        
            if not rank in ranks:
                ranks[rank] = 0
            ranks[rank] += 1


    result = hits/len(triplets_pred)

    rank_auc = compute_rank_roc(ranks,len(entities))

    
    submission = Submission.objects.get(pk=submission_id)
    submission.hits_10 = result
    submission.auc = rank_auc
    submission.save()

    return result
