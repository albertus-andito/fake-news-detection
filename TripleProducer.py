from json import JSONDecodeError
from nltk.tokenize import sent_tokenize, word_tokenize
from TripleExtractors import StanfordExtractor, IITExtractor
import json
import neuralcoref
import pprint
import requests
import spacy


class TripleProducer:
    """
    TripleProducer produces SPO triples from sentences, where the Subjects and Objects are linked to DBpedia
    entity resources. and the Predicates (Relations) are linked to DBpedia Ontology, whenever possible.

    :param extractor_type: SPO extractor tool. 'stanford_openie' or 'iit_openie' can be chosen as the SPO extractor,
    defaults to 'iit_openie' for now.
    :type extractor_type: str
    :param extraction_scope: The scope of the extraction, deciding whether it should include only relations between
    'named_entities', 'noun_phrases', or 'all', defaults to 'named entities' for now.
    :type extraction_scope: str

    """
    SPOTLIGHT_URL = 'https://api.dbpedia-spotlight.org/en/annotate?'

    def __init__(self, extractor_type=None, extraction_scope=None):
        """
        Constructor method
        """
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
        """
        Produce triples extracted from the document that are processed through the pipeline.
        The triples produced are in the form of:
        [ {'subject': subject, 'relation': relation, 'object':[object_1, object2, ...]},
          ...
        ]

        The Subjects and Objects are linked to DBpedia entity resources, while the Relations are linked to DBpedia
        Ontology, whenever possible.

        :param document: raw texts of document
        :type document: str
        :return: a list of triples, as explained
        :rtype: list
        """
        spacy_doc = self.nlp(document)

        # coreference resolution
        document = self.coref_resolution(spacy_doc)

        # extract spo triples from sentences
        all_triples = self.extract_triples(document)

        # remove stopwords from Subject and Object if scope is 'named_entities' or 'noun_phrases'
        if self.extraction_scope != 'all':
            all_triples = self.remove_stopwords(all_triples)

        # filter subjects and objects according to extraction_scope
        if self.extraction_scope == 'named_entities':
            all_triples = self.filter_in_named_entities(spacy_doc, all_triples)
        elif self.extraction_scope == 'noun_phrases':
            all_triples = self.filter_in_noun_phrases(spacy_doc, all_triples)
        # TODO: combined extraction scopes of named_entities and noun_phrases?

        # map to dbpedia resource (dbpedia spotlight) for Named Entities
        all_triples = self.spot_entities_with_context(document, all_triples)

        # lemmatise relations
        all_triples = self.lemmatise_relation(spacy_doc, all_triples)

        # TODO: might still want to match subject/object to DBpedia, even if they're not really named entities?
        # TODO: extract relation???
        return all_triples

    def coref_resolution(self, spacy_doc):
        """
        Perform coreference resolution on the document using neuralcoref.
        :param spacy_doc: document
        :type spacy_doc: spacy.tokens.Doc
        :return: Unicode representation of the doc where each corefering mention is replaced by the main mention in the
        associated cluster.
        """
        return spacy_doc._.coref_resolved

    def extract_triples(self, document):
        """
        Extract triples from document using the implementation of TripleExtractor.
        :param document: document
        :type document: str
        :return: a list of raw triples
        :rtype: list
        """
        sentences = sent_tokenize(document)
        triples = []
        for sentence in sentences:
            try:
                triples.append(self.extractor.extract(sentence))
            except JSONDecodeError as e:
                print(e.msg)
        return [triple for sentence in triples for triple in sentence]

    def remove_stopwords(self, all_triples):
        """
        Remove stopwords from individual Subject and Object.
        Currently, this is only done when the extraction scope is 'named_entities' or 'noun_phrases'.
        :param all_triples: a list of triples
        :type all_triples: list
        :return: a list of triples in which stopwords have been removed from the Subjects and Objects
        :rtype: list
        """
        all_stopwords = self.nlp.Defaults.stop_words
        for triple in all_triples:
            triple['subject'] = ' '.join([word for word in word_tokenize(triple['subject']) if word not in all_stopwords])
            # triple['relation'] = ' '.join([word for word in word_tokenize(triple['relation']) if word not in all_stopwords])
            triple['object'] = [' '.join([word for word in word_tokenize(o) if word not in all_stopwords]) for o in triple['object']]
        return all_triples

    def filter_in_named_entities(self, spacy_doc, all_triples):
        """
        Filter in only triples where the Subject and Object are both named entities
        :param spacy_doc: spacy document
        :type spacy_doc: spacy.tokens.Doc
        :param all_triples: a list of triples
        :type all_triples: list
        :return: a list of triples in which the Subjects and Objects are all named entities
        :rtype: list
        """
        entities = [ent.text for ent in spacy_doc.ents]
        return self.__filter(entities, all_triples)

    # spacy noun chunks is not accurate
    def filter_in_noun_phrases(self, spacy_doc, all_triples):
        """
        Filter in only triples where the Subject and Object are both noun phrases
        :param spacy_doc: spacy document
        :type spacy_doc: spacy.tokens.Doc
        :param all_triples: a list of triples
        :type all_triples: list
        :return: a list of triples in which the Subjects and Objects are all noun phrases
        :rtype: list
        """
        noun_phrases = [chunk.text for chunk in spacy_doc.noun_chunks]
        return self.__filter(noun_phrases, all_triples)

    def __filter(self, in_list, all_triples):
        """
        Filter in only triples where the Subject and Object are in the in_list argument.
        :param in_list: list of acceptable Subjects and Objects
        :type in_list: list
        :param all_triples: a list of triples
        :type all_triples: list
        :return: a list of triples in which the Subjects and Objects are all in the in_list argument
        :rtype: list
        """
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
        """
        Convert Subjects and Objects to DBpedia entity resources (i.e. in the form of 'http://dbpedia.org/resource/...'),
        if they are spotted using DBpedia Spotlight API.
        :param document: document
        :type document: str
        :param all_triples: a list of triples
        :type all_triples: list
        :return: a list of triples where the Subjects and Objects have been replaced with DBpedia entity resources,
        if possible
        :rtype: list
        """
        # Do we need to split the sentences first or not? May help with context if not?
        # sentences = sent_tokenize(document)
        try:
            response = requests.get(self.SPOTLIGHT_URL,
                                    params={'text': document},
                                    headers={'Accept': 'application/json'}).json()
        except json.decoder.JSONDecodeError as e:
            print(e.msg)
            response = None

        resources = response['Resources'] if 'Resources' in response else None

        if resources is not None:
            for triple in all_triples:
                for resource in resources:
                    if triple['subject'] in resource['@surfaceForm']:
                        triple['subject'] = resource['@URI']
                    objs = []
                    for obj in triple['object']:
                        if obj in resource['@surfaceForm']:
                            objs.append(resource['@URI'])
                        else:
                            objs.append(obj)
                    triple['object'] = objs

        return all_triples

    def lemmatise_relation(self, spacy_doc, all_triples):
        """
        Lemmatise relations to their based forms.
        :param spacy_doc: spacy document

        :param all_triples:
        :return:
        """
        all_stopwords = self.nlp.Defaults.stop_words
        for triple in all_triples:
            relation = [word for word in word_tokenize(triple['relation']) if word not in all_stopwords]
            triple['relation'] = ' '.join([spacy_tok.lemma_ for token in relation for spacy_tok in spacy_doc
                                           if token == spacy_tok.text])
        return all_triples


# Testing
if __name__ == "__main__":
    # iit_producer = TripleProducer(extraction_scope='noun_phrases')
    # stanford_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
    iit_producer = TripleProducer(extraction_scope='all')
    stanford_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='all')
    doc_1 = "Barrack Obama was born in Hawaii. He attended school in Jakarta."
    print(doc_1)
    print("IIT:")
    pprint.pprint(iit_producer.produce_triples(doc_1))
    print("Stanford:")
    pprint.pprint(stanford_producer.produce_triples(doc_1))

    # doc_2 = "Stores and supermarkets in Veracruz (Mexico) will close due to the new coronavirus. The local government " \
    #         "has asked people to buy supplies. "

    doc_2 = "Onion cures COVID19."
    print(doc_2)
    print("IIT:")
    pprint.pprint(iit_producer.produce_triples(doc_2))
    print("Stanford:")
    pprint.pprint(stanford_producer.produce_triples(doc_2))

    doc_3 = "Biomagnetism cures coronavirus."
    print(doc_3)
    print("IIT:")
    pprint.pprint(iit_producer.produce_triples(doc_3))
    print("Stanford:")
    pprint.pprint(stanford_producer.produce_triples(doc_3))

    doc_4 = "UV rays from the sun can cure COVID-19."
    print(doc_4)
    print("IIT:")
    pprint.pprint(iit_producer.produce_triples(doc_4))
    print("Stanford:")
    pprint.pprint(stanford_producer.produce_triples(doc_4))
