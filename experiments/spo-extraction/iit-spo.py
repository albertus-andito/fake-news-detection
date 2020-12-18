from pyopenie import OpenIE5
import pandas as pd

iit = OpenIE5('http://localhost:8000')

def extract_iit(sentence):
    print(sentence)
    spos = []
    extractions = iit.extract(sentence)
    for extraction in extractions:
        spo = {
            "subject": extraction['extraction']['arg1']['text'],
            "relation": extraction['extraction']['rel']['text'],
            "object": [obj['text'] for obj in extraction['extraction']['arg2s']]
        }
        spos.append(spo)
    return [spos]

df = pd.read_csv('./cleaned-COVID Fake News Data-spos.csv')
df["iit-openie"]=[extract_iit(sentence) for sentence in df["headlines"]]
df.to_csv('cleaned-COVID Fake News Data-spos.csv', index=False)