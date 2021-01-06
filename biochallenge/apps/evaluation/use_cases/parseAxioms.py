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
    triplets = read_file(in_file) 
    relations = Triplet.extract_relationships(triplets)
    print(relations)
    Triplet.to_file(triplets, out_file)

def read_file(in_file):
# To see which type of relationships are retrieved from the file take a look to doc in the Triplets class.
    file = open(in_file, 'r')

    triplets = []
    for line in file:
        triplet = Triplet.create_valid_triplet(line)
        if triplet != None:
            triplets.append(triplet)

    return triplets

def read_triplets_file(in_file):
# To see which type of relationships are retrieved from the file take a look to doc in the Triplets class.
    file = open(in_file, 'r')

    triplets = []
    for line in file:
        triplet = Triplet.read_triplet(line)
        triplets.append(triplet)

    return triplets


if __name__ == '__main__':
    main()

