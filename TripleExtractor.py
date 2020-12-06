from nltk import tokenize
from stanfordcorenlp import StanfordCoreNLP
import json
import neuralcoref
import pprint
import requests
import spacy

class TripleExtractor:
    openie_props = {'annotators': 'openie', 'pipelineLanguage': 'en', 'outputFormat': 'json'}
    spotlight_url = 'https://api.dbpedia-spotlight.org/en/annotate?'

    def __init__(self, coreNlpPath):
        self.coreNLP = StanfordCoreNLP(coreNlpPath)
        self.nlp = spacy.load('en')
        neuralcoref.add_to_pipe(self.nlp)
        self.i = 0;

    def __del__(self):
        self.coreNLP.close()

    def produce_triples(self, document):
        # coreference
        document = self.coref_resolution(document)

        all_triples = self.extract_triples(document)

        # map to dbpedia resource (dbpedia spotlight) for Named Entities
        all_triples = self.spot_entities_with_context(document, all_triples)

        # TODO: might still want to match subject/object to DBpedia, even if they're not really named entities?
        # TODO: extract relation???
        self.i +=1
        print(self.i)
        return all_triples

    def coref_resolution(self, document):
        doc = self.nlp(document)
        return doc._.coref_resolved

    def extract_triples(self, document):
        try:
            output_sentences = json.loads(self.coreNLP.annotate(document, self.openie_props), encoding='utf-8')['sentences']
        except json.decoder.JSONDecodeError as e:
            print(e.msg)
            return []
        all_triples = []
        for sentence in output_sentences:
            openie = sentence['openie']
            triples = []
            for openie_triple in openie:
                triple = {
                    "subject": openie_triple['subject'],
                    "relation": openie_triple['relation'],
                    "object": openie_triple['object']
                }
                triples.append(triple)
            all_triples.append(triples)
        return all_triples

    def spot_entities(self, all_triples):
        '''
            Matching named entities of subjects and objects to entities in DBpedia.
            This method is contextless, as it takes the subjects and objects individually, not from within a sentence.
        :param all_triples:
        :return:
        '''
        for sentence in all_triples:
            for triple in sentence:
                response = requests.get(self.spotlight_url,
                                        params={'text': triple['subject']},
                                        headers={'Accept': 'application/json'}).json()
                print(triple['subject'])
                pprint.pprint(response['Resources']) if 'Resources' in response else print("Wakwaw")
                response = requests.get(self.spotlight_url,
                                        params={'text': triple['object']},
                                        headers={'Accept': 'application/json'}).json()
                print(triple['object'])

    def spot_entities_with_context(self, document, all_triples):
        # Do we need to split the sentences first or not? May help with context if not?
        sentences = tokenize.sent_tokenize(document)
        for sentence, triples in zip(sentences, all_triples):
            try:
                response = requests.get(self.spotlight_url,
                                        params={'text': sentence},
                                        headers={'Accept': 'application/json'}).json()
            except json.decoder.JSONDecodeError as e:
                print(e.msg)
                response = None

            resources = response['Resources'] if 'Resources' in response else None

            if resources is not None:
                for triple in triples:
                    for resource in resources :
                        if triple['subject'] in resource['@surfaceForm']:
                            triple['subject'] = resource['@URI']
                        if triple['object'] in resource['@surfaceForm']:
                            triple['object'] = resource['@URI']

        return all_triples


if __name__ == "__main__":
    extractor = TripleExtractor(r'C:\Users\aandi\Documents\Uni\Final Year\FYP Code\stanford-corenlp-4.2.0')
    doc = "Barack Obama was born in Hawaii. He attended school in Jakarta."
    # doc = "Lionel Messi plays for Barcelona"
    # doc = "He was born in Washington"
    # triples = extractor.extract_triples(doc)
    # extractor.spot_entities(triples)
    # triples = extractor.spot_entities_with_context(doc, triples)
    # pprint.pprint(triples)

    triples = extractor.produce_triples(doc)
    pprint.pprint(triples)