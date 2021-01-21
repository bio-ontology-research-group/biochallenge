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

# def main(gt_file, pred_file, k):
#     print(compute_hits_k(gt_file, pred_file, k))


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
