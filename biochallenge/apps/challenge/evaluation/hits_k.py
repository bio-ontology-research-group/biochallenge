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

@ck.command()
@ck.option(
    '--gt-file',    '-gt',      default='example_gt.tsv',
    help = "Input file containing the new ground-truth relationships")
@ck.option(
    '--pred-file',  '-pred',    default='example_pred.tsv',
    help = "Input file containing the predcited relationships" )
@ck.option(
    '--k',          '-k',       default=10,
    help = "Value k of hits@k")
def main(gt_file, pred_file, k):
    print(compute_hits_k(gt_file, pred_file, k))


def compute_hits_k(gt_file, pred_file, k):

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

        scores = [-x.score for x in preds]   
        ranking = rankdata(scores, method='average')

        for i in range(len(preds)):
            rank = ranking[i]            
            pred = preds[i]
        
            if pred in gt and rank <= k:
                hits+=1
        
            if rank not in ranks:
                ranks[rank] = 0
            ranks[rank] += 1


    result = hits/len(triplets_pred)

    rank_auc = compute_rank_roc(ranks,len(triplets_pred))

    return result, rank_auc


def compute_rank_roc(ranks, n_preds):
    print(ranks)
    auc_x = list(ranks.keys())
    auc_x.sort()
    auc_y = []
    tpr = 0
    sum_rank = sum(ranks.values())
    for x in auc_x:
        tpr += ranks[x]
        auc_y.append(tpr / sum_rank)
    # auc_x.append(n_preds)
    # auc_y.append(1)
    print(auc_x)
    print(auc_y)
    auc = np.trapz(auc_y, auc_x) 
    return auc

if __name__ == "__main__":
    main()
