import click as ck

import sys
sys.path.append('../../')

from challenge.evaluation.parseAxioms import read_file, read_triplets_file
from scipy.stats import rankdata
from challenge.evaluation.triplets import Triplet
from time import sleep
from celery import shared_task, Celery
from django.apps import apps
import numpy as np
from functools import reduce

from joblib import Parallel, delayed
import multiprocessing
from collections import Counter

@ck.command()
@ck.option(
    '--gt-file',    '-gt',      default='data/example_gt.tsv',
    help = "Input file containing the new ground-truth relationships")
@ck.option(
    '--pred-file',  '-pred',    default='data/example_pred.tsv',
    help = "Input file containing the predcited relationships" )
@ck.option(
    '--k',          '-k',       default=10,
    help = "Value k of hits@k")

def main(gt_file, pred_file, k):
    print(compute_metrics(gt_file, pred_file, k))



def compute_metrics(gt_file, pred_file, k):

    #Computes hits@k and AUC


    #sleep(60)
    triplets_gt   = read_triplets_file(gt_file)
    triplets_pred = read_triplets_file(pred_file)

    entities = set([t.entity_1 for t in triplets_gt] + [t.entity_2 for t in triplets_gt])
    relations = set([t.relation for t in triplets_gt])
    print(len(entities), len(relations))


    ent1_rels = {}

    for triplet_gt in triplets_gt:
        ent1, rel = triplet_gt.entity_1, triplet_gt.relation

        if (ent1, rel) in ent1_rels:
            continue

        grouped_triplets_gt = set(filter(lambda x: x.entity_1 == ent1 and x.relation == rel, triplets_gt))
        grouped_triplets_pred = set(filter(lambda x: x.entity_1 == ent1 and x.relation == rel, triplets_pred))

        all_triplets =({Triplet(ent1, rel, ent2, 0) for ent2 in entities} - grouped_triplets_pred).union(grouped_triplets_pred)
        
        scores = [-x.score for x in all_triplets]   
        ranking = rankdata(scores, method='average')

        hits = 0
        ranks = {}
        
        for grouped_triplet in grouped_triplets_gt:
            idx = list(all_triplets).index(grouped_triplet)
            rank = ranking[idx]
            if rank <= k:
                
                hits+=1
            if not rank in ranks:
                ranks[rank] = 0
            ranks[rank] += 1

        ent1_rels[(ent1, rel)] = (hits, ranks)


    hits = map(lambda x: x[0], ent1_rels.values())
    hits =  reduce(lambda x,y: x+y, hits, 0)

    ranks = map(lambda x: x[1], ent1_rels.values())
    ranks = list(map(lambda x: Counter(x), ranks))
    ranks = dict(reduce(lambda x,y: x+y, ranks))

    result = hits/len(triplets_pred)

    rank_auc = compute_rank_roc(ranks,len(entities))

    

    return result, rank_auc


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

if __name__ == "__main__":
    main()
