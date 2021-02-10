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
from functools import reduce
from collections import Counter


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

    # Read test file (ground truth) and submission file (predictions).
    triplets_gt   = read_triplets_file(gt_file)
    triplets_pred = read_triplets_file(pred_file)

    entities = set([t.entity_1 for t in triplets_gt] + [t.entity_2 for t in triplets_gt] + [t.entity_1 for t in triplets_pred] + [t.entity_2 for t in triplets_pred])

    ent1_rels = {}

    for triplet_gt in triplets_gt:
        ent1, rel = triplet_gt.entity_1, triplet_gt.relation

        if (ent1, rel) in ent1_rels:
            continue

        #Extract triplets with fixed entity 1 and relation
        grouped_triplets_gt   = set(filter(lambda x: x.entity_1 == ent1 and x.relation == rel, triplets_gt))
        grouped_triplets_pred = set(filter(lambda x: x.entity_1 == ent1 and x.relation == rel, triplets_pred))

        all_triplets = ({Triplet(ent1, rel, ent2, score = 0) for ent2 in entities} - grouped_triplets_pred).union(grouped_triplets_pred)
        all_triplets = list(all_triplets)

        scores = [-x.score for x in all_triplets]   
        ranking = rankdata(scores, method='average')

        hits = 0
        ranks = {}
        
        for grouped_triplet in list(grouped_triplets_gt):
            idx = all_triplets.index(grouped_triplet)
            rank = ranking[idx]

            if rank <= k:
                hits+=1
            if not rank in ranks:
                ranks[rank] = 0
            ranks[rank] += 1

        ent1_rels[(ent1, rel)] = (hits, ranks)


    hits = map(lambda x: x[0], ent1_rels.values())
    hits =  reduce(lambda x,y: x+y, hits)

    ranks = map(lambda x: x[1], ent1_rels.values())
    ranks = list(map(lambda x: Counter(x), ranks))
    ranks = dict(reduce(lambda x,y: x+y, ranks))

    result = hits/len(triplets_pred)

    rank_auc = compute_rank_roc(ranks,len(entities))

    
    submission = Submission.objects.get(pk=submission_id)
    submission.hits_10 = result
    submission.auc = rank_auc
    submission.save()

   # return result
