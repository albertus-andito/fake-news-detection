import neuralcoref
import spacy
import os
import pprint

from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

if __name__ == '__main__':

    nlp = spacy.load('en_core_web_sm')
    neuralcoref.add_to_pipe(nlp)

    load_dotenv(dotenv_path=Path('../.env'))
    db_client = MongoClient(os.getenv('MONGODB_ADDRESS'))
    db = db_client['fnd']
    db_article_collection = db['articles']

    article = db_article_collection.find_one({'source': 'https://www.independent.co.uk/arts-entertainment/theatre-dance/news/sister-act-whoopi-goldberg-delay-tickets-london-b1802916.html'})['texts']
    pprint.pprint(article)

    spacy_doc = nlp(article)
    pprint.pprint(spacy_doc._.coref_resolved)