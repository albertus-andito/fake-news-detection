import os
from pathlib import Path
import pprint
from dotenv import load_dotenv
from nltk import sent_tokenize
from pymongo import MongoClient

from tripleproducer import TripleProducer

if __name__ == '__main__':
    tp = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')

    load_dotenv(dotenv_path=Path('../.env'))
    db_client = MongoClient(os.getenv('MONGODB_ADDRESS'))
    db = db_client['fnd']
    db_article_collection = db['articles']

    url = 'https://www.independent.co.uk/arts-entertainment/music/news/sarah-harding-cancer-update-girls-aloud-b1816748.html'
    article = db_article_collection.find_one({'source': url})['texts']

    spacy_doc = tp.nlp(article)
    original_sentences = sent_tokenize(article)

    # coreference resolution
    document = tp.coref_resolution(spacy_doc)
    # capitalise start of sentence
    coref_resolved_sentences = sent_tokenize(document)

    all_triples = tp.extract_triples(coref_resolved_sentences)

    filtered_triples = tp.filter_in_noun_phrases(spacy_doc, all_triples)

    final_triples = tp.produce_triples(article, extraction_scope='noun_phrases')

    for (sent, filtered) in zip(original_sentences, filtered_triples):
        pprint.pprint(sent)
        pprint.pprint(filtered)
        # pprint.pprint(final[1])