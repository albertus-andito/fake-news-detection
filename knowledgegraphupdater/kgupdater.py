import logging
import logging.config
import os

from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

from articlescraper.scrapers import Scrapers
from definitions import ROOT_DIR, LOGGER_CONFIG_PATH
from entitycorefresolver import EntityCorefResolver
from kgwrapper import KnowledgeGraphWrapper
from triple import Triple
from tripleproducer import TripleProducer


class KnowledgeGraphUpdater:
    """
    A Knowledge Graph Updater, which consists of all functionalities related to updating the knowledge graph.

    :param auto_update: whether the knowledge graph will be updated automatically once triples are extracted,
        or wait for user confirmation
    :type auto_update: bool
    """

    def __init__(self, auto_update=None):
        LOGFILE_PATH = os.path.join(ROOT_DIR, 'logs', 'kg-updater.log').replace("\\", "/")
        logging.config.fileConfig(LOGGER_CONFIG_PATH,
                                  defaults={'logfilename': LOGFILE_PATH},
                                  disable_existing_loggers=False)
        self.logger = logging.getLogger()

        load_dotenv(dotenv_path=Path('../.env'))
        self.db_client = MongoClient(os.getenv('MONGODB_ADDRESS'))
        self.db = self.db_client['fnd']
        self.db_article_collection = self.db['articles']
        self.db_article_collection.create_index('source', unique=True)
        self.db_triples_collection = self.db['triples']

        self.triple_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
        self.knowledge_graph = KnowledgeGraphWrapper()
        if auto_update is None:
            self.auto_update = False
        else:
            self.auto_update = auto_update
        self.coref_resolver = EntityCorefResolver()

        self.scrapers = Scrapers()

    def update_missed_knowledge(self, kg_auto_update=None, extraction_scope=None):
        """
        Extract triples from stored articles whose triples has not been extracted yet, and save the triples to the DB.
        If the auto_update mode is active, the non-conflicting triples are added automatically to the knowledge graph.

        :param kg_auto_update: an optional parameter that sets whether the non-conflicting triples are added to the
            knowledge graph or not. This will only matter if the auto_update field is False. If the auto_update field is
            already True, then this parameter will not be looked upon.
        :type kg_auto_update: bool
        :param extraction_scope: The scope of the extraction, deciding whether it should include only relations between
            'named_entities', 'noun_phrases', or 'all.
        :type extraction_scope: str
        """
        for article in self.db_article_collection.find({'triples': None}):
            try:
                self.__extract_and_save_triples(article['source'], article['texts'], extraction_scope, kg_auto_update)

            except Exception as e:
                self.logger.error("Exception occurred when extracting article " + article['source'] + ": " + e.__str__())

    def __extract_and_save_triples(self, url, texts, extraction_scope, kg_auto_update):
        """
        Private method to extract triples and an article given the URL and save the triples to DB.
        Non-conflicting triples are added to knowledge graph if kg_auto_update is True.

        :param url: URL of article whose triples are going to be extracted
        :type url: str
        :param texts: article text whose triples are going to be extracted
        :type texts: str
        :param extraction_scope: The scope of the extraction, deciding whether it should include only relations between
            'named_entities', 'noun_phrases', or 'all.
        :type extraction_scope: str
        :param kg_auto_update: whether the non-conflicting triples are added to the knowledge graph or not.
        :type kg_auto_update: bool
        """
        self.logger.info('Extracting triples for article: %s', url)
        # set 'added' to False for all triples initially
        triples = [{'sentence': results[0],
                    'triples': [{**triple.to_dict(), **{'added': False}} for triple in results[1]]}
                   for results in self.triple_producer.produce_triples(texts,
                                                                       extraction_scope=extraction_scope)]
        for sentence in triples:
            for triple in sentence['triples']:
                exists = self.knowledge_graph.check_triple_object_existence(Triple.from_dict(triple))
                # The exact triple already exists in the KG. Mark as added.
                if exists is True:
                    triple['added'] = True

        self.db_article_collection.update_one({'source': url}, {'$set': {'triples': triples}})

        if (kg_auto_update is None and self.auto_update) or kg_auto_update:
            self.logger.info('Inserting non conflicting knowledge for ' + url)
            self.insert_all_nonconflicting_knowledge(url)

    def insert_all_nonconflicting_knowledge(self, article_url):
        """
        Insert non-conflicting triples of an article to the knowledge graph.

        :param article_url: URL of the article source
        :type article_url: str
        """
        article = self.db_article_collection.find_one({'source': article_url})
        for sentence in article['triples']:
            for triple in sentence['triples']:
                if self.knowledge_graph.check_triple_object_existence(Triple.from_dict(triple)):
                    triple['added'] = True
                else:
                    conflicts = self.knowledge_graph.get_triples(triple['subject'], triple['relation'], transitive=True)
                    # if triple not in conflicts:
                    if conflicts is None or len(conflicts) < 1:
                        self.knowledge_graph.insert_triple_object(Triple.from_dict(triple))
                        triple['added'] = True
                    else:
                        triple['added'] = False
        self.db_article_collection.update_one({'source': article['source']}, {'$set': {'triples': article['triples']}})

    def delete_all_knowledge_from_article(self, article_url):
        """
        Delete triples that are extracted from an article, from the knowledge graph.
        Triples from the articles must have been extracted beforehand and stored in DB.

        :param article_url: URL of the article source
        :type article_url: str
        """
        self.logger.info('Deleting triples of article: %s', article_url)
        article = self.db_article_collection.find_one({'source': article_url})
        if 'triples' in article:
            for sentence in article['triples']:
                self.delete_knowledge(sentence['triples'])

    def delete_knowledge(self, triples):
        """
        Remove triples from knowledge graph.

        :param triples: list of triples (in the form of dictionaries)
        :type triples: list
        """
        for triple in triples:
            self.knowledge_graph.delete_triple_object(Triple.from_dict(triple), transitive=True)
            # Need to update both triples from articles and from user input. We don't know where the triple was from.
            self.db_article_collection.update_many({'triples': {'$exists': True}},
                                                   {'$set': {'triples.$[].triples.$[triple].added': False}},
                                                   array_filters=[{'triple.subject': triple['subject'],
                                                                   'triple.relation': triple['relation'],
                                                                   'triple.objects': triple['objects']
                                                                   }])
            self.db_triples_collection.update_one({'subject': triple['subject'],
                                                   'relation': triple['relation'],
                                                   'objects': triple['objects']},
                                                  {'$set': {'added': False}})

    def get_article_pending_knowledge(self, article_url):
        """
        Returns all pending triples (that are not currently in the knowledge graph) for the specified article.

        :param article_url: URL of the article source
        :type article_url: str
        :return: list of pending triples extracted from the article if exist, or None
        :rtype: list or None
        """
        article = self.db_article_collection.find_one({'source': article_url, 'triples': {'$exists': True}})
        if article is not None:
            return [{'sentence': sentence['sentence'],
                     'triples': [triple for triple in sentence['triples'] if triple['added'] is False]}
                    for sentence in article['triples']]

    def delete_article_pending_knowledge(self, article_url, triples):
        """
        Deletes pending article triples, that have been added to the knowledge graph, from the database.

        :param article_url: URL of the article source
        :type article_url: str
        :param triples: list of pending triples to be deleted
        :type triples: list
        """
        for sentence in triples:
            for triple in sentence['triples']:
                self.db_article_collection.update_one({'source': article_url},
                                                      {'$pull': {'triples.$[sentence].triples':
                                                                     {'subject': triple['subject'],
                                                                      'relation': triple['relation'],
                                                                      'objects': triple['objects']}}},
                                                      array_filters=[{'sentence.sentence': sentence['sentence']}])

    def get_all_pending_knowledge(self):
        """
        Returns all pending triples (that are not currently in the knowledge graph) for all scraped articles.

        :return: list of all pending triples extracted from all articles
        :rtype: list
        """
        # TODO: add pagination
        articles = []
        for article in self.db_article_collection.find({'triples': {'$exists': True}}):
            pending = [{'sentence': sentence['sentence'],
                        'triples': [triple for triple in sentence['triples'] if triple['added'] is False]}
                       for sentence in article['triples']]
            # pending = [triple for triple in article['triples'] if triple['added'] is False]
            if len(pending) > 0:
                articles.append({
                    'source': article['source'],
                    'triples': pending
                })
        return articles

    def get_article_knowledge(self, article_url):
        """
        Returns all triples of that have been extracted from the specified article, regardless of whether the triple
        has been added to the knowledge graph or not.

        :param article_url: URL of the article source
        :type article_url: str
        :return: list of triples extracted from the article if exist, or None
        :rtype: list or None
        """
        article = self.db_article_collection.find_one({'source': article_url, 'triples': {'$exists': True}})
        if article is None:
            return None
        return article['triples']

    def get_all_articles_knowledge(self):
        """
        Returns all triples that have been extracted from all scraped articles.

        :return: list of all triples extracted from all articles
        :rtype: list
        """
        # This function is memory expensive if the list is huge. It's better to add pagination etc.
        # TODO: add pagination
        return list(
            self.db_article_collection.find({'triples': {'$exists': True}}, {'source': 1, 'triples': 1, '_id': 0}))

    def get_all_unresolved_corefering_entities(self):
        """
        Returns all unresolved corefering entities extracted from articles.

        :return: list of unresolved corefering entities
        :rtype: list
        """
        articles = []
        for article in self.db_article_collection.find({'coref_entities': {'$exists': True}}):
            entities = [{'main': ent['main'],
                         'mentions': [mention for mention in ent['mentions'] if mention['resolved'] is False]}
                        for ent in article['coref_entities']]
            entities = [ent for ent in entities if len(ent['mentions']) > 0]
            articles.append({
                'source': article['source'],
                'coref_entities': entities
            })
        return articles

    def insert_entities_equality(self, entity_a, entity_b):
        """
        Resolve two entities as the same.

        :param entity_a: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity_a: str
        :param entity_b: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity_b: str
        """
        self.knowledge_graph.add_sameAs_relation(entity_a, entity_b)

    def insert_articles_knowledge(self, articles_triples):
        """
        Insert triples that are related to an article to the knowledge graph.
        If the triple has conflict, mark the conflict as 'added' in the db.
        If the triple doesn't exist on db, add the triple to the db.

        :param articles_triples: dictionary of article triples
        :type articles_triples: dict
        """
        for article in articles_triples:
            stored_triples = self.db_article_collection.find_one({'source': article['source']})['triples']
            for sentence in article['triples']:
                stored_sentence = next((sent_triples for sent_triples in stored_triples
                                        if sent_triples['sentence'] == sentence['sentence']), None)
                for triple in sentence['triples']:
                    # FIXME: check for conflict? probably no need to
                    self.knowledge_graph.insert_triple_object(Triple.from_dict(triple))
                    if stored_sentence is not None and triple in stored_sentence['triples']:
                        self.db_article_collection.update_many({'source': article['source']},
                                                               {'$set': {
                                                                   'triples.$[].triples.$[triple].added': True}},
                                                               array_filters=[
                                                                   {'triple.subject': triple['subject'],
                                                                    'triple.relation': triple['relation'],
                                                                    'triple.objects': triple['objects']
                                                                    }]
                                                               )

                    # new triple from existing sentence
                    elif stored_sentence is not None:
                        self.db_article_collection.update_one({'source': article['source'],
                                                               'triples': {'$elemMatch':
                                                                               {'sentence': stored_sentence[
                                                                                   'sentence']}}},
                                                              {'$push': {'triples.$.triples':
                                                                             {'subject': triple['subject'],
                                                                              'relation': triple['relation'],
                                                                              'objects': triple['objects'],
                                                                              'added': True}}}
                                                              )
                        # may need to check other sentences, or even articles for the same triple
                    # new triple from non-existing sentence
                    else:
                        # accommodate triples about the article that are manually inserted
                        self.db_article_collection.update_one({'source': article['source']},
                                                              {'$push': {'triples': {'sentence': '', 'triples': [
                                                                  {'subject': triple['subject'],
                                                                   'relation': triple['relation'],
                                                                   'objects': triple['objects'],
                                                                   'added': True}]}
                                                                         }})
                        # may need to check other sentences, or even articles for the same triple

    def insert_knowledge(self, triple, check_conflict):
        """
        Insert triple to the knowledge graph.

        :param triple: the triple to be inserted to the knowledge graph
        :type triple: dict
        :param check_conflict: whether it should check for conflicts first or not.
        :type check_conflict: bool
        :return: list of conflicts if there are conflicts and check_conflict is True, None otherwise
        :rtype: list or None
        """
        self.db_triples_collection.replace_one({'subject': triple['subject'],
                                                'relation': triple['relation'],
                                                'objects': triple['objects']},
                                               triple, upsert=True)
        if check_conflict:
            # check if the exact triples are already in the knowledge graph?
            exists = self.knowledge_graph.check_triple_object_existence(Triple.from_dict(triple))
            if not exists:
                conflicts = self.knowledge_graph.get_triples(triple['subject'], triple['relation'])
                if conflicts is not None:
                    return conflicts
        self.knowledge_graph.insert_triple_object(Triple.from_dict(triple))
        self.db_triples_collection.update_one({'subject': triple['subject'],
                                               'relation': triple['relation'],
                                               'objects': triple['objects']},
                                              {'$set': {'added': True}})

    def get_knowledge(self, subject, relation, objects=None):
        """
        Returns triple from the knowledge graph that has the given conditions.
        If objects are given, it will return back the triple if it exist in the knowledge graph.

        :param subject: subject of the triple in DBpedia format
        :type subject: str
        :param relation: relation of the triple in DBpedia format
        :type relation: str
        :param objects: (list) of objects of the triple in DBpedia format, this parameter is optional
        :type objects: list or str
        :return: list of triples
        :rtype: list
        """
        if objects is None:
            return [triple.to_dict() for triple in self.knowledge_graph.get_triples(subject, relation)]
        if type(objects) is str:
            objects = [objects]
        triple = Triple(subject, relation, objects)
        if self.knowledge_graph.check_triple_object_existence(triple):
            return [triple.to_dict()]

    def get_entity(self, subject):
        """
        Returns all triples that has the subject parameter as the subject.

        :param subject: subject in DBpedia format
        :type subject: str
        :return: list of Triples
        :rtype: list
        """
        return self.knowledge_graph.get_entity(subject)

    def get_all_articles(self):
        """
        Returns all articles' URLs, headlines, and dates, in the form of dictionaries.

        :return: list of dictionaries of articles
        :rtype: list
        """
        # TODO: pagination
        articles = []
        for article in self.db_article_collection.find({},
                                                       {'_id': False, 'source': True, 'date': True, 'headlines': True}):
            articles.append({
                'source': article['source'],
                'headlines': '. '.join(article['headlines']),
                'date': article['date'].timestamp()
            })
        return articles

    def extract_new_article(self, url, extraction_scope='noun_phrases', kg_auto_update=False):
        """
        Scrape an article given the URL and extract the triples from the article.

        :param url: URL of article whose triples are going to be extracted
        :type url: str
        :param extraction_scope: The scope of the extraction, deciding whether it should include only relations between
            'named_entities', 'noun_phrases', or 'all.
        :type extraction_scope: str
        :param kg_auto_update: whether the non-conflicting triples are added to the knowledge graph or not.
        :type kg_auto_update: bool
        """
        article = self.scrapers.scrape_text_from_url(url, save_to_db=True)
        try:
            self.__extract_and_save_triples(url, article, extraction_scope, kg_auto_update)
        except Exception as e:
            self.logger.error("Exception occured when extracting article " + url + ": " + e.__str__())

    def get_all_extracted_articles(self):
        """
        Returns all articles' URLs, headlines, and dates, whose triples have been extracted,
        in the form of dictionaries.

        :return: list of dictionaries of articles
        :rtype: list
        """
        # TODO: pagination
        articles = []
        for article in self.db_article_collection.find({'triples': {'$exists': True}},
                                                       {'_id': False, 'source': True, 'date': True, 'headlines': True}):
            articles.append({
                'source': article['source'],
                'headlines': '. '.join(article['headlines']),
                'date': article['date'].timestamp()
            })
        return articles
