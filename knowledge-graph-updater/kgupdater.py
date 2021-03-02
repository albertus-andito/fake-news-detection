import logging
import logging.config
import os
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

from definitions import ROOT_DIR, LOGGER_CONFIG_PATH
from entitycorefresolver import EntityCorefResolver
from kgwrapper import KnowledgeGraphWrapper
from triple import Triple
from tripleproducer import TripleProducer


# TODO: Haven't considered the headlines, only the texts for now. Might want to include the headlines to be extracted.

class KnowledgeGraphUpdater:
    """
    A Knowledge Graph Updater, which updates the knowledge graph using knowledge from the scraped articles.

    :param auto_update: whether the knowledge graph will be updated automatically, or wait for user confirmation
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

    def update_missed_knowledge(self, kg_auto_update=None, extraction_scope=None):
        """
        Extract triples from stored articles whose triples has not been extracted yet, and save the triples to the DB.
        Triples that have conflicts in the knowledge graph are identified.
        If the auto_update mode is active, the non-conflicting triples are added to the knowledge graph.
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
                self.logger.info('Extracting triples for article: %s', article['source'])
                # set 'added' to False for all triples initially
                triples = [{'sentence': results[0],
                            'triples': [{**triple.to_dict(), **{'added': False}} for triple in results[1]]}
                           for results in self.triple_producer.produce_triples(article['texts'],
                                                                               extraction_scope=extraction_scope)]

                conflicted_triples = []
                for sentence in triples:
                    for triple in sentence['triples']:
                        exists = self.knowledge_graph.check_triple_object_existence(Triple.from_dict(triple))
                        # The exact triple already exists in the KG. Mark as added.
                        if exists is True:
                            triple['added'] = True
                        # check for conflict
                        else:
                            conflicts = self.knowledge_graph.get_triples(triple['subject'], triple['relation'])
                            if conflicts is not None:
                                a_triple = triple.copy()
                                del a_triple['added']
                                for conflict in conflicts:
                                    conflicted_triples.append(
                                        {'toBeInserted': a_triple, 'inKnowledgeGraph': conflict.to_dict()})

                self.logger.debug('Found conflicts for article %s: %s', article['source'], conflicted_triples)

                self.db_article_collection.update_one({'source': article['source']}, {'$set': {'triples': triples}})

                if len(conflicted_triples) > 0:  # save conflicts
                    self.db_article_collection.update_one({'source': article['source']},
                                                          {'$set': {'conflicts': conflicted_triples}})

                if (kg_auto_update is None and self.auto_update) or kg_auto_update:
                    self.logger.info('Inserting non conflicting knowledge for ' + article['source'])
                    self.insert_all_nonconflicting_knowledge(article['source'])

                # Get all DBpedia entities from the article's triples
                entities = []
                for sentence in triples:
                    for triple in sentence['triples']:
                        entities.append(triple['subject'])
                        for obj in triple['objects']:
                            if obj.startswith('http://dbpedia.org/resource/'):
                                entities.append(obj)

                # Include only corefering entities that exist in the extracted triples
                coref_clusters = [{'main': main,
                                   'mentions': [{
                                       'mention': mention,
                                       'resolved': self.knowledge_graph.check_sameAs_relation(main, mention)}
                                       for mention in mentions]}
                                  for main, mentions in
                                  self.coref_resolver.get_coref_clusters(article['texts']).items()
                                  if main in entities]
                if len(coref_clusters) > 0:
                    self.db_article_collection.update_one({'source': article['source']},
                                                          {'$set': {'coref_entities': coref_clusters}})

            except Exception as e:
                self.logger.error("Exception occured when extracting article " + article['source'] + ": " + e.__str__())

    def insert_all_nonconflicting_knowledge(self, article_url):
        """
        Insert non-conflicting triples of an article to the knowledge graph.
        :param article_url: URL of the article source
        :type article_url: str
        """
        article = self.db_article_collection.find_one({'source': article_url})
        if 'conflicts' in article:
            conflicts = [conflict['toBeInserted'] for conflict in article['conflicts']]
        else:
            conflicts = []

        for sentence in article['triples']:
            for triple in sentence['triples']:
                # We need to delete the 'added' field first because we want to check equality with 'conflicts' list.
                # By default, the 'added' field should have been False anyway at this stage, because the triple hasn't been
                # inserted.
                del triple['added']
                if triple not in conflicts:
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
        :param triples: list of triples (in form of dictionaries)
        :type triples: list
        """
        for triple in triples:
            self.knowledge_graph.delete_triple_object(Triple.from_dict(triple))
            # Need to update both triples from articles and from user input. We don't know where the triple was from.
            self.db_article_collection.update_many({},
                                                   {'$set': {'triples.$[].triples.$[triple].added': False}},
                                                   array_filters=[{'triple.subject': triple['subject'],
                                                                   'triple.relation': triple['relation'],
                                                                   'triple.objects': triple['objects']
                                                                   }])
            # TODO: do we need to care about 'added' in 'conflicts' field?
            self.db_article_collection.update_many({'conflicts':
                {'$elemMatch':
                    {'inKnowledgeGraph': {
                        'subject': triple['subject'],
                        'relation': triple['relation'],
                        'objects': triple['objects']}
                    }
                }
            },
                {'$set': {'conflicts.$': None}})
            self.db_article_collection.update_many({}, {'$pull': {'conflicts': None}})
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
        :return:
        """
        for sentence in triples:
            for triple in sentence['triples']:
                self.db_article_collection.update_one({'source': article_url},
                                                      {'$pull': {'triples.$[sentence].triples':
                                                                     {'subject': triple['subject'],
                                                                      'relation': triple['relation'],
                                                                      'objects': triple['objects']}}},
                                                      array_filters=[{'sentence.sentence': sentence['sentence']}])
                self.db_article_collection.update_one({'source': article_url},
                                                      {'$pull': {'conflicts':
                                                          {'toBeInserted': {
                                                              'subject': triple['subject'],
                                                              'relation': triple['relation'],
                                                              'objects': triple['objects']}
                                                          }
                                                      }})

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

    def get_article_conflicts(self, article_url):
        """
        Returns conflicted triples of the specified article.
        In this case, conflict means that subject and relation of a triple have already existed in the knowledge graph.
        :param article_url: URL of the article source
        :type article_url: str
        :return: list of conflicted triples (in form of dictionaries) if exist, or None
        :rtype: list or None
        """
        article = self.db_article_collection.find_one({'source': article_url, 'conflicts': {'$exists': True}})
        if article is None:
            return None
        return article['conflicts']

    def get_all_article_conflicts(self):
        """
        Returns all conflicted triples of all scraped articles.
        :return: list of conflicted triples (in form of dictionaries, with their source article url)
        :rtype: list
        """
        # This function is memory expensive if the list is huge. It's better to add pagination etc.
        # TODO: add pagination
        articles = []
        for article in self.db_article_collection.find({'conflicts': {'$exists': True}}):
            articles.append({
                'source': article['source'],
                'conflicts': article['conflicts']
            })
        return articles

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
                                                                   # {'sentence.sentence': stored_sentence['sentence']},
                                                                   {'triple.subject': triple['subject'],
                                                                    'triple.relation': triple['relation'],
                                                                    'triple.objects': triple['objects']
                                                                    }]
                                                               )
                        self.db_article_collection.update_many({'source': article['source'],
                                                                'conflicts':
                                                                    {'$elemMatch':
                                                                        {'toBeInserted': {
                                                                            'subject': triple['subject'],
                                                                            'relation': triple['relation'],
                                                                            'objects': triple['objects']}
                                                                        }
                                                                    }
                                                                },
                                                               {'$set': {'conflicts.$.added': True}})
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
        :param triple:
        :param check_conflict: whether it should check for conflicts first or not.
        :type check_conflict: bool
        :return: list of conflicts if there are conflicts and check_conflict is True, None otherwise
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
        :param subject:
        :param relation:
        :param objects: optional
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
        :param subject: subject in dbpedia format
        :type subject: str
        :return: list of Triples
        :rtype: list
        """
        return self.knowledge_graph.get_entity(subject)


if __name__ == '__main__':
    kgu = KnowledgeGraphUpdater()
    # kgu.update_missed_knowledge()
    # kgu.delete_all_knowledge_from_article("https://www.bbc.co.uk/news/world-us-canada-55210243")

    # pprint.pprint(kgu.get_all_pending_knowledge())

    # kgu.insert_articles_knowledge([{
    #     "source": "https://www.bbc.co.uk/news/world-us-canada-55210243",
    #     "triples": [
    #         {
    #             "subject": "http://dbpedia.org/resource/Mr_Giuliani",
    #             "relation": "http://dbpedia.org/ontology/repeat",
    #             "objects": ["unsubstantiated claims"],
    #             "added": False
    #         }
    #     ]
    # }])

    kgu.delete_knowledge([{
        "subject": "http://dbpedia.org/resource/Mr_Giuliani",
        "relation": "http://dbpedia.org/ontology/repeat",
        "objects": ["unsubstantiated claims"],
    }])
