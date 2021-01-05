class Triplet():
    
    def __init__(self, entity_1, relation, entity_2):
        self.entity_1 = entity_1
        self.relation = relation
        self.entity_2 = entity_2        

    def __str__(self):
        return '\t'.join((self.entity_1, self.relation, self.entity_2))

    @classmethod
    def create_valid_triplet(cls, string):
        # will try to parse axioms of the form: "ENTITY_1 SubClassOf RELATION some ENTITY_2"
        words = string.rstrip('\n').split(' ')

        if len(words) == 5 and words[1] == "SubClassOf" and words[3] == "some":
            entity_1 = words[0]
            relation = words[2]
            entity_2 = words[4]

            return cls(entity_1, relation, entity_2)
        
        else:
            return None