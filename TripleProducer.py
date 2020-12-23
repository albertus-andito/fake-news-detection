from json import JSONDecodeError
from nltk import tokenize
from TripleExtractors import StanfordExtractor, IITExtractor
import json
import neuralcoref
import pprint
import requests
import spacy


class TripleProducer:
    SPOTLIGHT_URL = 'https://api.dbpedia-spotlight.org/en/annotate?'

    def __init__(self, extractor_type=None, extraction_scope=None):
        if extractor_type == 'stanford_openie':
            self.extractor = StanfordExtractor()
        elif extractor_type == 'iit_openie' or extractor_type is None:
            self.extractor = IITExtractor()
        else:
            raise ValueError("The extractor_type is unrecognised. Use 'stanford_openie' or 'iit_openie'.")

        self.extraction_scope = 'named_entities' if extraction_scope is None else extraction_scope
        if self.extraction_scope not in ['named_entities', 'noun_phrases', 'all']:
            raise ValueError("The extraction_scope is unrecognised. Use 'named_entities', 'noun_phrases', or 'all'.")

        self.nlp = spacy.load('en')
        neuralcoref.add_to_pipe(self.nlp)

    def produce_triples(self, document):
        spacy_doc = self.nlp(document)

        # coreference
        document = self.coref_resolution(spacy_doc)

        # extract spo triples from sentences
        all_triples = self.extract_triples(document)

        if self.extraction_scope == 'named_entities':
            all_triples = self.filter_in_named_entities(spacy_doc, all_triples)
        elif self.extraction_scope == 'noun_phrases':
            all_triples = self.filter_in_noun_phrases(spacy_doc, all_triples)
        # TODO: combined extraction scopes of named_entities and noun_phrases?

        # map to dbpedia resource (dbpedia spotlight) for Named Entities
        # all_triples = self.spot_entities_with_context(document, all_triples)

        # TODO: might still want to match subject/object to DBpedia, even if they're not really named entities?
        # TODO: extract relation??? get present tense of verb?
        return all_triples

    def coref_resolution(self, spacy_doc):
        return spacy_doc._.coref_resolved

    def extract_triples(self, document):
        sentences = tokenize.sent_tokenize(document)
        triples = []
        for sentence in sentences:
            try:
                triples.append(self.extractor.extract(sentence))
            except JSONDecodeError as e:
                print(e.msg)
        return [triple for sentence in triples for triple in sentence]

    def filter_in_named_entities(self, spacy_doc, all_triples):
        entities = [ent.text for ent in spacy_doc.ents]
        pprint.pprint(entities)
        pprint.pprint(all_triples)
        return self.__filter(entities, all_triples)

    def filter_in_noun_phrases(self, spacy_doc, all_triples):
        noun_phrases = [chunk.text for chunk in spacy_doc.noun_chunks]
        pprint.pprint(noun_phrases)
        pprint.pprint(all_triples)
        return self.__filter(noun_phrases, all_triples)

    def __filter(self, in_list, all_triples):
        filtered_triples = []
        for triple in all_triples:
            if triple['subject'] in in_list:
                for obj in triple['object']:
                    if obj in in_list:
                        filtered_triples.append(triple)
                        break
        return filtered_triples

    # def spot_entities(self, all_triples):
    #     '''
    #         Matching named entities of subjects and objects to entities in DBpedia.
    #         This method is contextless, as it takes the subjects and objects individually, not from within a sentence.
    #     :param all_triples:
    #     :return:
    #     '''
    #     for sentence in all_triples:
    #         for triple in sentence:
    #             response = requests.get(self.spotlight_url,
    #                                     params={'text': triple['subject']},
    #                                     headers={'Accept': 'application/json'}).json()
    #             print(triple['subject'])
    #             pprint.pprint(response['Resources']) if 'Resources' in response else print("Wakwaw")
    #             response = requests.get(self.spotlight_url,
    #                                     params={'text': triple['object']},
    #                                     headers={'Accept': 'application/json'}).json()
    #             print(triple['object'])

    def spot_entities_with_context(self, document, all_triples):
        # Do we need to split the sentences first or not? May help with context if not?
        sentences = tokenize.sent_tokenize(document)
        for sentence, triples in zip(sentences, all_triples):
            try:
                response = requests.get(self.SPOTLIGHT_URL,
                                        params={'text': sentence},
                                        headers={'Accept': 'application/json'}).json()
            except json.decoder.JSONDecodeError as e:
                print(e.msg)
                response = None

            resources = response['Resources'] if 'Resources' in response else None

            if resources is not None:
                for triple in triples:
                    for resource in resources:
                        if triple['subject'] in resource['@surfaceForm']:
                            triple['subject'] = resource['@URI']
                        if triple['object'] in resource['@surfaceForm']:
                            triple['object'] = resource['@URI']

        return all_triples


if __name__ == "__main__":
    iit_producer = TripleProducer(extraction_scope='noun_phrases')
    stanford_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
    doc_1 = "Barrack Obama was born in Hawaii. He attended school in Jakarta."
    print(doc_1)
    print("IIT:")
    pprint.pprint(iit_producer.produce_triples(doc_1))
    print("Stanford:")
    pprint.pprint(stanford_producer.produce_triples(doc_1))

    # doc_2 = "Stores and supermarkets in Veracruz (Mexico) will close due to the new coronavirus. The local government " \
    #         "has asked people to buy supplies. "
    # doc_2 = "Biomagnetism cures coronavirus."
    # doc_2 = "UV rays from the sun can cure COVID-19."
    doc_2 = "Onion cures COVID19."
    print(doc_2)
    print("IIT:")
    pprint.pprint(iit_producer.produce_triples(doc_2))
    print("Stanford:")
    pprint.pprint(stanford_producer.produce_triples(doc_2))
