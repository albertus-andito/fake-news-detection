# Script to get SPO triples from first dataset (from https://zenodo.org/record/4282522)

from TripleProducer import TripleProducer
import pprint
import pandas as pd

df = pd.read_csv('../../covid-dataset/cleaned-COVID Fake News Data.csv')

def get_relations(triples):
    relation = []
    for sent in triples:
        for triple in sent:
            relation.append(triple['relation'])
    return relation

extractor = TripleProducer(r'C:\Users\aandi\Documents\Uni\Final Year\FYP Code\stanford-corenlp-4.2.0')
df['triples'] = [extractor.produce_triples(doc) for doc in df['headlines']]
pprint.pprint(df['triples'])
print(df['triples'].loc[1][0])
print(df['triples'].loc[2][0])
df['relations'] = df['triples'].apply(lambda x: get_relations(x))
print(df['relations'])
df.to_csv('cleaned-COVID Fake News Data-with-relations.csv', index=False)