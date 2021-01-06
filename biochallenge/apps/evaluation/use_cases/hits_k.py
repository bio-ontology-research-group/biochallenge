import click as ck
from parseAxioms import read_file, read_triplets_file
from scipy.stats import rankdata
from triplets import Triplet

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
            print(pred, ranking[i])
            if pred in gt and ranking[i] <= k:
                hits+=1
        
    
    result = hits/len(triplets_gt)

    print(result)

if __name__ == "__main__":
    main()