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
    '--gt-file',    '-gt',      default='example_gt.tsv',
    help = "Input file containing the new ground-truth relationships")
@ck.option(
    '--pred-file',  '-pred',    default='example_pred.tsv',
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


    def check_entity_1(ent1):
        hits = 0
        ranks = {}
        print(ent1)
        for rel in relations:
            
            triplets = []
            for ent2 in entities:
                
                triplet =  Triplet(ent1, rel, ent2, score = 0)

                try:
                    idx_pred =  triplets_pred.index(triplet)
                except:
                    idx_pred = None

                if idx_pred != None:
                    triplet.score = triplets_pred[idx_pred].score

                triplets.append(triplet)

            scores = [-x.score for x in triplets]   
            ranking = rankdata(scores, method='average')

            for i in range(len(ranking)):
                rank = ranking[i]            
                pred = triplets[i]
            
                if pred in triplets_gt and rank <= k:
                    hits+=1
            
                    if not rank in ranks:
                        ranks[rank] = 0
                    ranks[rank] += 1
        return hits, ranks


    num_cores = 15
    results = Parallel(n_jobs=num_cores)(delayed(check_entity_1)(ent1) for ent1 in entities)

    hits =  reduce(lambda x,y: x+y, map(lambda x: x[0], results))

    ranks = map(lambda x: x[1], results)
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
