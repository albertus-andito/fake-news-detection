import logging
import logging.config
import os
from json import JSONDecodeError
from nltk.tokenize import word_tokenize
from spacy.matcher import Matcher

from definitions import ROOT_DIR, LOGGER_CONFIG_PATH
from triple import Triple
from tripleextractors import StanfordExtractor, IITExtractor
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
    FALCON_URL = 'https://labs.tib.eu/falcon/api?mode=long'

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

        LOGFILE_PATH = os.path.join(ROOT_DIR, 'logs', 'triple-producer.log').replace("\\", "/")
        logging.config.fileConfig(LOGGER_CONFIG_PATH,
                                  defaults={'logfilename': LOGFILE_PATH},
                                  disable_existing_loggers=False)
        self.logger = logging.getLogger()

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
        original_sentences = list(spacy_doc.sents)

        # coreference resolution
        document = self.coref_resolution(spacy_doc)
        coref_resolved_sentences = [s.text for s in self.nlp(document).sents]

        # extract spo triples from sentences
        all_triples = self.extract_triples(coref_resolved_sentences)

        # filter subjects and objects according to extraction_scope
        if self.extraction_scope == 'named_entities':
            all_triples = self.filter_in_named_entities(spacy_doc, all_triples)
        elif self.extraction_scope == 'noun_phrases':
            all_triples = self.filter_in_noun_phrases(spacy_doc, all_triples)
        # TODO: combined extraction scopes of named_entities and noun_phrases?

        # remove stopwords from Subject and Object if scope is 'named_entities' or 'noun_phrases'
        if self.extraction_scope != 'all':
            all_triples = self.remove_stopwords(all_triples)

        # map to dbpedia resource (dbpedia spotlight) for Named Entities
        all_triples = self.spot_entities_with_context(document, all_triples)

        # link relations using Falcon
        triples_with_linked_relations = self.link_relations(coref_resolved_sentences, all_triples)
        # triples_with_linked_relations = None

        # lemmatise relations
        all_triples = self.lemmatise_relations(spacy_doc, all_triples)

        # convert relations to dbpedia format
        all_triples = self.convert_relations(all_triples)

        # combine triples whose relations are manually derived with triples whose relations derived by falcon
        if triples_with_linked_relations is not None and len(triples_with_linked_relations) > 0:
            all_triples = [list(set(ori_triples + falcon_triples))
                           for ori_triples, falcon_triples in zip(all_triples, triples_with_linked_relations)]

        # Subject needs to be a DBpedia resource/entity
        all_triples = self.convert_subjects(all_triples)

        if len(original_sentences) != len(all_triples):
            self.logger.error("Problem occurred during sentenization! Different lengths of sentences identified.")
            raise Exception("Different length between sentences and triples")

        return [*zip(original_sentences, all_triples)]

    def coref_resolution(self, spacy_doc):
        """
        Perform coreference resolution on the document using neuralcoref.
        :param spacy_doc: document
        :type spacy_doc: spacy.tokens.Doc
        :return: Unicode representation of the doc where each corefering mention is replaced by the main mention in the
        associated cluster.
        """
        return spacy_doc._.coref_resolved

    def extract_triples(self, sentences):
        """
        Extract triples from document using the implementation of TripleExtractor.
        :param sentences: list of document sentences
        :type sentences: list
        :return: a list of list of raw triples (top-level list represents sentences)
        :rtype: list
        """
        try:
            triples = [self.extractor.extract(sentence) for sentence in sentences]
            return triples
        except JSONDecodeError as e:
            self.logger.error(e.msg)

    def remove_stopwords(self, all_triples):
        """
        Remove stopwords from individual Subject and Object.
        Currently, this is only done when the extraction scope is 'named_entities' or 'noun_phrases'.
        :param all_triples: a list of list of triples (top-level list represent sentences)
        :type all_triples: list
        :return: a list of list of triples in which stopwords have been removed from the Subjects and Objects
        :rtype: list
        """
        all_stopwords = self.nlp.Defaults.stop_words
        for sentence in all_triples:
            for triple in sentence:
                triple.subject = ' '.join([word for word in word_tokenize(triple.subject) if word not in all_stopwords])
                # triple.relation = ' '.join([word for word in word_tokenize(triple['relation']) if word not in all_stopwords])
                triple.objects = [' '.join([word for word in word_tokenize(o) if word not in all_stopwords]) for o in
                                  triple.objects]
        return all_triples

    def filter_in_named_entities(self, spacy_doc, all_triples):
        """
        Filter in only triples where the Subject and Object are both named entities
        :param spacy_doc: spacy document
        :type spacy_doc: spacy.tokens.Doc
        :param all_triples: a list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: a list of list of triples in which the Subjects and Objects are all named entities
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
        :param all_triples: a list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: a list of list of triples in which the Subjects and Objects are all noun phrases
        :rtype: list
        """
        noun_phrases = [chunk.text for chunk in spacy_doc.noun_chunks]
        return self.__filter(noun_phrases, all_triples)

    def __filter(self, in_list, all_triples):
        """
        Filter in only triples where the Subject and Object are in the in_list argument.
        :param in_list: list of acceptable Subjects and Objects
        :type in_list: list
        :param all_triples: a list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: a list of list of triples in which the Subjects and Objects are all in the in_list argument
        :rtype: list
        """
        filtered_triples_sentences = []
        for sentence in all_triples:
            filtered_triples = []
            for triple in sentence:
                if any(triple.subject in word or word in triple.subject for word in in_list):
                    for obj in triple.objects:
                        if any(obj in word or word in obj for word in in_list):
                            filtered_triples.append(triple)
                            break
            filtered_triples_sentences.append(filtered_triples)
        return filtered_triples_sentences

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
        :param all_triples: a list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: a list of list of triples where the Subjects and Objects have been replaced with DBpedia entity resources,
        if possible
        :rtype: list
        """
        # Do we need to split the sentences first or not? May help with context if not?
        # sentences = sent_tokenize(document)
        response = requests.get(self.SPOTLIGHT_URL,
                                    params={'text': document},
                                    headers={'Accept': 'application/json'})
        if response.status_code != 200:
            self.logger.error(response.text)
        try:
            response = response.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(e.msg)
            response = None

        if response is None:
            return all_triples
        resources = response['Resources'] if 'Resources' in response else None
        if resources is None:
            return all_triples

        entities = {resource['@surfaceForm']: resource['@URI'] for resource in resources}
        for sentence in all_triples:
            for triple in sentence:
                if entities.get(triple.subject):
                    triple.subject = entities.get(triple.subject)
                else:
                    triple.subject = self.__find_uri(triple.subject, entities)
                triple.objects = [entities.get(obj, self.__find_uri(obj, entities)) for obj in triple.objects]

        return all_triples

    def __find_uri(self, obj, entities):
        """
        Find DBpedia resource for a given subject/object where the DBpedia resource is a substring of the subject/object.
        If such resource does not exist, return the original subject/object.
        :param obj: subject/object
        :type obj: str
        :param entities: a dictionary of entities as keys and their DBpedia URI as items
        :type entities: dict
        :return: the DBpedia resource if exist, otherwise, return the original subject/object
        :rtype: str
        """
        candidates = [uri for surfaceForm, uri in entities.items() if surfaceForm in obj]
        if len(candidates) > 0:
            # Only getting index [0] might be unacceptable if there are multiple candidates
            return candidates[0]
        return obj

    def link_relations(self, sentences, all_triples):
        """
        Link relations to DBpedia Ontology using Falcon (https://labs.tib.eu/falcon/), if available.
        :param sentences: list of document sentences
        :type sentences: list
        :param all_triples: list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: new list of list of triples with dbpedia relations
        :rtype list
        """
        new_triples = []
        for sentence, triples in zip(sentences, all_triples):
            falcon_triples = []
            relations = []
            try:
                response = requests.post(self.FALCON_URL,
                                     data='{"text": "%s"}' % self.__fix_encoding(sentence),
                                     headers={"Content-Type": "application/json"})
            except Exception as e:
                self.logger.error(e)
            if response.status_code != 200:
                self.logger.error(response.text)
            else:
                try:
                    relations = response.json()["relations"]
                except json.decoder.JSONDecodeError as e:
                    self.logger.error(e.msg)
                    return None

            if len(relations) > 0:
                dbpedia_relations = [rel[0] for rel in relations]
                raw_relations = [rel[1] for rel in relations]
                # check triples whose relation is a substring of raw_relation
                falcon_triples = [Triple(triple.subject, dbpedia_relations[raw_relations.index(triple.relation)], triple.objects)
                                  for triple in triples if triple.relation in raw_relations]
                # check triples who have raw_relation as a substring of their relation
                for i, rel in enumerate(raw_relations):
                    existed_triples = [triple for triple in triples if rel in triple.relation]
                    falcon_triples += [Triple(triple.subject, dbpedia_relations[i], triple.objects)
                                       for triple in existed_triples]
            new_triples.append(falcon_triples)

        return new_triples

    def __fix_encoding(self, sentence):
        return sentence.replace('"', '\\"')\
                       .replace('“', '\\"')\
                       .replace('”', '\\"')\
                       .replace('’', '\'')\
                       .replace('–', '-')

    def lemmatise_relations(self, spacy_doc, all_triples):
        """
        Lemmatise relations to their based forms.
        :param spacy_doc: spacy document
        :type spacy_doc: spacy.tokens.Doc
        :param all_triples: list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: list of list of triples where relations have been lemmatised
        :rtype: list
        """
        all_stopwords = self.nlp.Defaults.stop_words
        for sentence in all_triples:
            for triple in sentence:
                relation = [word for word in word_tokenize(triple.relation.replace('[', '').replace(']', '')) if
                            word not in all_stopwords]
                triple.relation = ' '.join([self.__get_lemma(token, spacy_doc) for token in relation])
                if not triple.relation:
                    triple.relation = "is"
        return all_triples

    def __get_lemma(self, token, spacy_doc):
        matcher = Matcher(self.nlp.vocab)
        matcher.add(token, None, [{"TEXT": token}])
        if len(matcher(spacy_doc)) == 0:
            return ''
        match = (matcher(spacy_doc)[0])
        return spacy_doc[match[1]:match[2]].lemma_

    def convert_relations(self, all_triples):
        """
        Prepend all relations with "http://dbpedia.org/ontology/", even if the relation doesn't exist in DBpedia.
        :param all_triples: list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: list of list of triples, where relations have been converted
        :rtype: list
        """
        for sentence in all_triples:
            for triple in sentence:
                triple.relation = "http://dbpedia.org/ontology/" + self.__camelise(triple.relation).lstrip()
        return all_triples

    def __camelise(self, sentence):
        """
        Util function to convert words into camelCase
        :param sentence: sentence
        :type sentence: str
        :return: camelCase words
        :rtype: str
        """
        words = word_tokenize(sentence)
        if len(words) == 1:
            return sentence.lower()
        else:
            s = "".join(word[0].upper() + word[1:].lower() for word in words)
            return s[0].lower() + s[1:]
        
    def convert_subjects(self, all_triples):
        """
        Prepend all subjects with "http://dbpedia.org/resource/" if the subject hasn't been spotted yet as a DBpedia entity.
        :param all_triples: list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: list of list of triples, where all subjects are dbpedia resources
        :rtype: list
        """
        dbpedia = "http://dbpedia.org/resource/"
        for sentence in all_triples:
            for triple in sentence:
                if not triple.subject.startswith(dbpedia):
                    triple.subject = dbpedia+triple.subject.replace(" ", "_")
        return all_triples


# Testing
if __name__ == "__main__":
    # iit_producer = TripleProducer(extraction_scope='noun_phrases')
    # stanford_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
    iit_producer = TripleProducer(extraction_scope='all')
    stanford_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='all')
    doc_1 = "Barrack Obama was born in Hawaii. He attended school in Jakarta. Mr. Obama was the president of the USA."
    # doc_1 = "Barrack Obama was born in Hawaii. Obama lives."
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
