import logging
import logging.config
import os
from json import JSONDecodeError
from nltk.tokenize import sent_tokenize, word_tokenize
from spacy.matcher import Matcher

from definitions import ROOT_DIR, LOGGER_CONFIG_PATH
from kgwrapper import KnowledgeGraphWrapper
from triple import Triple
from tripleextractors import StanfordExtractor, IITExtractor
from utils import convert_to_dbpedia_ontology

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
        # Triple extractor setup
        if extractor_type == 'stanford_openie':
            self.extractor = StanfordExtractor()
        elif extractor_type == 'iit_openie' or extractor_type is None:
            self.extractor = IITExtractor()
        else:
            raise ValueError("The extractor_type is unrecognised. Use 'stanford_openie' or 'iit_openie'.")

        # Extraction scope setup
        self.extraction_scope = 'named_entities' if extraction_scope is None else extraction_scope
        if self.extraction_scope not in ['named_entities', 'noun_phrases', 'all']:
            raise ValueError("The extraction_scope is unrecognised. Use 'named_entities', 'noun_phrases', or 'all'.")

        # Knowledge graph setup
        self.knowledge_graph = KnowledgeGraphWrapper()

        # Spacy setup
        self.nlp = spacy.load('en_core_web_sm')
        neuralcoref.add_to_pipe(self.nlp)
        self.all_stopwords = self.nlp.Defaults.stop_words
        self.all_stopwords.discard('not')

        # Logger setup
        LOGFILE_PATH = os.path.join(ROOT_DIR, 'logs', 'triple-producer.log').replace("\\", "/")
        logging.config.fileConfig(LOGGER_CONFIG_PATH,
                                  defaults={'logfilename': LOGFILE_PATH},
                                  disable_existing_loggers=False)
        self.logger = logging.getLogger()

    def produce_triples(self, document, extraction_scope=None):
        """
        Produce triples extracted from the document that are processed through the pipeline.
        The triples produced are in the form of:
        [ (sentence, [{'subject': subject, 'relation': relation, 'object':[object_1, object2, ...], ...]),
          ...
        ]

        The Subjects and Objects are linked to DBpedia entity resources, while the Relations are linked to DBpedia
        Ontology, whenever possible.

        :param document: raw texts of document
        :type document: str
        :param extraction_scope: The scope of the extraction, deciding whether it should include only relations between
        'named_entities', 'noun_phrases', or 'all. Defaults to the extraction_scope member variable.
        :type extraction_scope: str
        :return: a list of tuples, of sentence and its triples, as explained
        :rtype: list
        """
        extraction_scope = self.extraction_scope if extraction_scope is None else extraction_scope
        if extraction_scope not in ['named_entities', 'noun_phrases', 'all']:
            raise ValueError("The extraction_scope is unrecognised. Use 'named_entities', 'noun_phrases', or 'all'.")

        spacy_doc = self.nlp(document)
        original_sentences = sent_tokenize(document)

        # coreference resolution
        document = self.coref_resolution(spacy_doc)
        # capitalise start of sentence
        coref_resolved_sentences = sent_tokenize(self.__capitalise_sentence_start(document))

        # extract spo triples from sentences
        all_triples = self.extract_triples(coref_resolved_sentences)

        # filter subjects and objects according to extraction_scope
        if extraction_scope == 'named_entities':
            all_triples = self.filter_in_named_entities(spacy_doc, all_triples)
        elif extraction_scope == 'noun_phrases':
            all_triples = self.filter_in_noun_phrases(spacy_doc, all_triples)
            # all_triples = self.filter_noun_phrases(all_triples)
        # TODO: combined extraction scopes of named_entities and noun_phrases?

        # remove stopwords from Subject and Object if scope is 'named_entities' or 'noun_phrases'
        # (removing stopwords doesn't always make sense. What if the stopwords are meant to be in the noun phrase
        # or named entities anyway?)
        # if extraction_scope != 'all':
        #     all_triples = self.remove_stopwords(all_triples)

        # map to dbpedia resource (dbpedia spotlight) for Named Entities
        all_triples = self.spot_entities_with_context(document, all_triples)

        # map to dbpedia resource that does not exists locally, not in spotlight
        # subjects need to be dbpedia resource
        all_triples = self.spot_local_entities(all_triples)

        # link relations using Falcon
        # triples_with_linked_relations = self.link_relations(coref_resolved_sentences, all_triples)
        triples_with_linked_relations = None

        # lemmatise relations
        all_triples = self.lemmatise_relations(spacy_doc, all_triples)

        # convert relations to dbpedia format
        all_triples = self.convert_relations(all_triples)

        # combine triples whose relations are manually derived with triples whose relations derived by falcon
        if triples_with_linked_relations is not None and len(triples_with_linked_relations) > 0:
            all_triples = [list(set(ori_triples + falcon_triples))
                           for ori_triples, falcon_triples in zip(all_triples, triples_with_linked_relations)]
        else:
            all_triples = [list(set(triples)) for triples in all_triples]

        # remove triples with empty component
        all_triples = self.remove_empty_components(all_triples)

        self.logger.info(all_triples)
        if len(original_sentences) != len(all_triples):
            self.logger.error("Problem occurred during sentenization! Different lengths of sentences identified.")
            raise Exception("Different length between sentences and triples")

        results = [(sentence, triples) for (sentence, triples) in zip(original_sentences, all_triples) if
                   len(triples) > 0]

        return results

    def coref_resolution(self, spacy_doc):
        """
        Perform coreference resolution on the document using neuralcoref.
        :param spacy_doc: document
        :type spacy_doc: spacy.tokens.Doc
        :return: Unicode representation of the doc where each corefering mention is replaced by the main mention in the
        associated cluster.
        """
        return spacy_doc._.coref_resolved

    def __capitalise_sentence_start(self, document):
        sentences = document.split('. ')
        capitalised = [sentence[0].capitalize() + sentence[1:] for sentence in sentences if len(sentence) > 0]
        return '. '.join(capitalised)

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
            self.logger.error('Triple extraction erro')

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
        Filter in only triples where the Subject and Object are both (in the list of) noun phrases.
        The list of noun phrases is generated from the spacy document.
        :param spacy_doc: spacy document
        :type spacy_doc: spacy.tokens.Doc
        :param all_triples: a list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: a list of list of triples in which the Subjects and Objects are all noun phrases
        :rtype: list
        """
        noun_phrases = [chunk.text.lower() for chunk in spacy_doc.noun_chunks]
        return self.__filter(noun_phrases, all_triples)

    def filter_noun_phrases(self, all_triples):
        """
        Filter in only triples where the Subject and Object are both noun phrases.
        Whether subject or object is a noun phrase or not is determined by making each subject and object into Spacy
        document, and then check if it is a noun phrase or not, or if it is a noun or not.
        Due to the Spacy document being created for all subjects and objects, this method is slower than the other
        method above.
        :param all_triples: a list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: a list of list of triples in which the Subjects and Objects are all noun phrases
        :rtype: list
        """
        filtered_triples_sentences = []
        for sentence in all_triples:
            filtered_triples = []
            for triple in sentence:
                s_noun_phrases = [chunk.text for chunk in self.nlp(triple.subject).noun_chunks]
                s_noun_phrases += [token.text for token in self.nlp(triple.subject) if (token.pos_ == 'NOUN'
                                   or token.pos_ == 'PROPN') and token.text not in s_noun_phrases]
                if triple.subject in s_noun_phrases:
                    for obj in triple.objects:
                        o_noun_phrases = [chunk.text for chunk in self.nlp(obj).noun_chunks]
                        o_noun_phrases += [token.text for token in self.nlp(obj) if (token.pos_ == 'NOUN'
                                           or token.pos_ == 'PROPN') and token.text not in o_noun_phrases]
                        if obj in o_noun_phrases:
                            filtered_triples.append(triple)
                            break
            filtered_triples_sentences.append(filtered_triples)
        return filtered_triples_sentences

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
                if triple.subject.lower() in in_list or any(triple.subject.lower() in token for token in in_list):
                    # if any(triple.subject in word or word in triple.subject for word in in_list):
                    for obj in triple.objects:
                        if obj.lower() in in_list or any(obj.lower() in token for token in in_list):
                            # if any(obj in word or word in obj for word in in_list):
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

    def spot_local_entities(self, all_triples):
        """
        Prepend all subjects with "http://dbpedia.org/resource/" if the subject hasn't been spotted yet as a DBpedia entity.
        For objects, check first if such entity exists in the local knowledge graph (may not exist in DBpedia Spotlight KG).
        If yes, convert the object to the DBpedia resource format.
        :param all_triples: list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: list of list of triples, where all subjects are dbpedia resources
        and objects that exist in the local KG also converted to dbpedia resources
        :rtype: list
        """
        dbpedia = "http://dbpedia.org/resource/"
        for sentence in all_triples:
            for triple in sentence:
                # subject needs to be resource, regardless of its existence
                if not triple.subject.startswith(dbpedia):
                    triple.subject = dbpedia + triple.subject.replace(" ", "_")
                triple.objects = [dbpedia + obj.replace(" ", "_") if obj and not obj.startswith(dbpedia) and
                                  self.knowledge_graph.check_resource_existence(dbpedia + obj.replace(" ", "_"))
                                  else obj for obj in triple.objects]
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
                falcon_triples = [
                    Triple(triple.subject, dbpedia_relations[raw_relations.index(triple.relation)], triple.objects)
                    for triple in triples if triple.relation in raw_relations]
                # check triples who have raw_relation as a substring of their relation
                for i, rel in enumerate(raw_relations):
                    existed_triples = [triple for triple in triples if rel in triple.relation]
                    falcon_triples += [Triple(triple.subject, dbpedia_relations[i], triple.objects)
                                       for triple in existed_triples]
            new_triples.append(falcon_triples)

        return new_triples

    def __fix_encoding(self, sentence):
        return sentence.replace('"', '\\"') \
            .replace('“', '\\"') \
            .replace('”', '\\"') \
            .replace('’', '\'') \
            .replace('–', '-')

    def lemmatise_relations(self, spacy_doc, all_triples):
        """
        Lemmatise relations to their base forms.
        :param spacy_doc: spacy document
        :type spacy_doc: spacy.tokens.Doc
        :param all_triples: list of list of triples (top-level list represents sentences)
        :type all_triples: list
        :return: list of list of triples where relations have been lemmatised
        :rtype: list
        """
        for sentence in all_triples:
            for triple in sentence:
                if triple.relation == 'is in':
                    triple.relation = 'in'
                else:
                    relation = [word for word in word_tokenize(triple.relation.replace('[', '').replace(']', ''))]
                    if len(relation) > 1:
                        relation = [word for word in relation if word not in self.all_stopwords]
                    triple.relation = ' '.join([self.__get_lemma(token, spacy_doc) for token in relation])
                    if not triple.relation or triple.relation == 'be':
                        triple.relation = 'is'
        return all_triples

    def __get_lemma(self, token, spacy_doc):
        """
        Find the lemma based on the token's appearence in the text
        :param token:
        :param spacy_doc:
        :return: lemma of the token
        """
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
                triple.relation = convert_to_dbpedia_ontology(triple.relation)
        return all_triples

    def remove_empty_components(self, all_triples):
        return [[triple for triple in sentence
                 if triple.subject != '' and triple.relation != '' and all(obj != '' for obj in triple.objects)]
                for sentence in all_triples]

    # def convert_subjects(self, all_triples):
    #     """
    #     Prepend all subjects with "http://dbpedia.org/resource/" if the subject hasn't been spotted yet as a DBpedia entity.
    #     :param all_triples: list of list of triples (top-level list represents sentences)
    #     :type all_triples: list
    #     :return: list of list of triples, where all subjects are dbpedia resources
    #     :rtype: list
    #     """
    #     dbpedia = "http://dbpedia.org/resource/"
    #     for sentence in all_triples:
    #         for triple in sentence:
    #             if not triple.subject.startswith(dbpedia):
    #                 triple.subject = dbpedia + triple.subject.replace(" ", "_")
    #     return all_triples


# Testing
if __name__ == "__main__":
    # iit_producer = TripleProducer(extraction_scope='noun_phrases')
    stanford_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
    # iit_producer = TripleProducer(extraction_scope='all')
    # stanford_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='all')
    doc_1 = "Barrack Obama was born in Hawaii. He attended school in Jakarta. Mr Obama was the president of the USA. " \
            "Mr Obama stayed in White House for 8 years."
    # doc_1 = "Barrack Obama was born in Hawaii. Obama lives."
    print(doc_1)
    # print("IIT:")
    # pprint.pprint(iit_producer.produce_triples(doc_1))
    print("Stanford:")
    pprint.pprint(stanford_producer.produce_triples(doc_1))

    doc = "President Donald Trump's personal lawyer, Rudy Giuliani, has tested positive for Covid-19 and is being treated in hospital.  Mr Giuliani, who has led the Trump campaign's legal challenges to the election results, is the latest person close to the president to be infected.  Since November, he has been on a cross-country tour in an effort to convince state governments to overturn the vote. Like other Trump officials, he has been criticised for shunning face masks. Mr Trump, who was ill with the virus in October, announced the diagnosis in a tweet, writing: \"Get better soon Rudy, we will carry on!\" Mr Giuliani, 76, was admitted to the Medstar Georgetown University Hospital in Washington DC on Sunday. The news came after Mr Giuliani had visited Arizona, Georgia and Michigan all in the past week - where he spoke to government officials while not wearing masks. Following news of Mr Giuliani's diagnosis, the Arizona legislature announced sudden plans to shut down for one week. Several Republican lawmakers there had spent over 10 hours with the former New York mayor last week discussing election results.  Following Mr Giuliani's visit to Phoenix, Arizona, the state's Republican party tweeted a photo of him with other mask-less state lawmakers. In a tweet, Mr Giuliani thanked well-wishers for their messages, and said he was \"recovering quickly\".   His son, Andrew Giuliani, who works at the White House and tested positive for the virus last month, tweeted that his father was \"resting, getting great care and feeling well\".  It is not clear if Mr Giuliani is experiencing symptoms or when he caught the virus.  Nearly 14.6 million people have been infected with Covid-19 in the US, according to Johns Hopkins University, and 281,234 people have died - the highest figures of any country in the world. On Sunday, Dr Deborah Birx, the White House coronavirus task force co-ordinator, criticised the Trump administration for flouting guidelines and peddling \"myths\" about the pandemic.  \"I hear community members parroting back those situations, parroting back that masks don't work, parroting back that we should work towards herd immunity,\" Dr Birx told NBC. \"This is the worst event that this country will face,\" she said. Since the 3 November election, Mr Giuliani has travelled the country as part of unsuccessful efforts to overturn Mr Trump's election defeat. During many of his events, he was seen without a face mask and ignoring social distancing.  Last Wednesday, he appeared at a hearing on alleged election fraud in Michigan where he asked a witness beside him if she would be comfortable removing her face mask. \"I don't want you to do this if you feel uncomfortable, but would you be comfortable taking your mask off, so we can hear you more clearly?\" said Mr Giuliani, who was not wearing a face mask. The witness chose to keep her mask on after asking the panel if she could be heard. On Thursday Mr Giuliani travelled to Georgia where he repeated unsubstantiated claims of voter fraud at a Senate committee hearing about election security.  Dozens of people in Mr Trump's orbit are said to have tested positive for Covid-19 since October.  Boris Epshteyn, another Trump adviser, tested positive shortly after appearing alongside Rudy Giuliani at a news conference on 25 November. Others include the president's chief of staff Mark Meadows and press secretary Kayleigh McEnany, along with his wife Melania and sons Donald Jnr and Baron. Mr Trump's own diagnosis and hospital stay upended his campaign for a second term in office, less than a month before he faced Joe Biden in the presidential election. Mr Trump has refused to concede, insisting without evidence that the election was stolen or rigged. Attorney General William Barr said last week that his department had not seen any evidence of widespread voter fraud that would change the result. Mr Biden will be sworn in as president on 20 January."
    pprint.pprint(stanford_producer.produce_triples(doc))
    # doc_2 = "Stores and supermarkets in Veracruz (Mexico) will close due to the new coronavirus. The local government " \
    #         "has asked people to buy supplies. "

    # doc_2 = "Onion cures COVID19."
    # print(doc_2)
    # print("IIT:")
    # pprint.pprint(iit_producer.produce_triples(doc_2))
    # print("Stanford:")
    # pprint.pprint(stanford_producer.produce_triples(doc_2))
    #
    # doc_3 = "Biomagnetism cures coronavirus."
    # print(doc_3)
    # print("IIT:")
    # pprint.pprint(iit_producer.produce_triples(doc_3))
    # print("Stanford:")
    # pprint.pprint(stanford_producer.produce_triples(doc_3))
    #
    # doc_4 = "UV rays from the sun can cure COVID-19."
    # print(doc_4)
    # print("IIT:")
    # pprint.pprint(iit_producer.produce_triples(doc_4))
    # print("Stanford:")
    # pprint.pprint(stanford_producer.produce_triples(doc_4))
