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
import requests
import gzip
from urllib import parse


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


def execute_sparql(endpoint, query, format):
    query_url="{endpoint}?query={query}&format={format}&timeout=0" \
                .format(
                    endpoint=endpoint, 
                    query=parse.quote(query), 
                    format=parse.quote(format), 
                    )
    response = requests.get(query_url, stream=True)
    return response
        
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

    os.makedirs(release.get_dir(), exist_ok=True)
    res = execute_sparql(release.sparql_endpoint, release.sparql_query, 'csv')
    data_file = os.path.join(release.get_dir(), 'data.csv.gz')
    with gzip.open(data_file, 'wb') as f:
        res.raise_for_status()
        for chunk in res.iter_content(chunk_size=65536):
            f.write(chunk)
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
