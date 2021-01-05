import click as ck
from triplets import Triplet

@ck.command()
@ck.option(
    '--in-file', '-in', default='axioms.txt',
    help = "Input file containing all the relationships in the KG" )
@ck.option(
    '--out-file', '-out', default='rels.tsv',
    help = "Output file containing the relationships recognized by Triplets class" )


def main(in_file, out_file):
    getRelationships(in_file, out_file)


def getRelationships(in_file, out_file):
# To see which type of relationships are retrieved from the file take a look to doc in the Triplets class.
    file = open(in_file, 'r')

    triplets = []
    for line in file:
        triplet = Triplet.create_valid_triplet(line)
        if triplet != None:
            triplets.append(str(triplet))


    with open(out_file, 'w') as f:
        for triplet in triplets:
            f.write(triplet+'\n')



if __name__ == '__main__':
    main()

