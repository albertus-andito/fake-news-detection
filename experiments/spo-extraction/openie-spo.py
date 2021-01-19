from stanfordcorenlp import StanfordCoreNLP
import pandas as pd
import json

stanford = StanfordCoreNLP(r'C:\Users\aandi\Documents\Uni\Final Year\FYP Code\stanford-corenlp-4.2.0')
stanford_props={'annotators': 'openie', 'pipelineLanguage': 'en', 'outputFormat': 'json'}

def extract_stanford(sentence):
    print(sentence)
    spos = []
    try:
        annotation = json.loads(stanford.annotate(sentence, properties=stanford_props))["sentences"]
    except json.decoder.JSONDecodeError as e:
        print(e.msg)
        return []
    for sent in annotation:
        for openie in sent['openie']:
            spo = {
                    "subject": openie['subject'],
                    "relation": openie['relation'],
                    "object": openie['object']
            }
            spos.append(spo)
    return [spos]

df = pd.read_csv('../../../covid-dataset/cleaned-COVID Fake News Data.csv')
df["stanford-openie"]=[extract_stanford(sentence) for sentence in df["headlines"]]
df.to_csv('cleaned-COVID Fake News Data-spos.csv', index=False)