import textacy
import pandas as pd

def extract_textacy(sentence):
    print(sentence)
    spos = []
    doc = textacy.make_spacy_doc(sentence, lang="en")
    svos = textacy.extract.subject_verb_object_triples(doc)
    for svo in svos:
        spo = {
            "subject": svo[0],
            "relation": svo[1],
            "object": svo[2]
        }
        spos.append(spo)
    return [spos]

df = pd.read_csv('./cleaned-COVID Fake News Data-spos.csv')
df["textacy"]=[extract_textacy(sentence) for sentence in df["headlines"]]
df.to_csv('cleaned-COVID Fake News Data-spos.csv', index=False)