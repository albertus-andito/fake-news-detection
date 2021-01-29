import logging.config
import os
import pprint
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

from definitions import ROOT_DIR, LOGGER_CONFIG_PATH
from kgwrapper import KnowledgeGraphWrapper
from triple import Triple
from tripleproducer import TripleProducer


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
        self.db_client = MongoClient(os.getenv("MONGODB_ADDRESS"))
        self.db = self.db_client["fnd"]
        self.db_article_collection = self.db["articles"]
        self.db_article_collection.create_index("source", unique=True)
        self.db_triples_collection = self.db["triples"]

        self.triple_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
        self.knowledge_graph = KnowledgeGraphWrapper()
        if auto_update is None:
            self.auto_update = False
        else:
            self.auto_update = auto_update

    def update_missed_knowledge(self):
        """
        Extract triples from stored articles whose triples has not been extracted yet, and save the triples to the DB.
        Triples that have conflicts in the knowledge graph are identified.
        If the auto_update mode is active, the triples are added to the knowledge graph.
        """
        for article in self.db_article_collection.find({"triples": None}):
            print(' '.join(article["texts"]))
            triples = [{**triple.to_dict(), **{"added": False}} for triple in
                       self.triple_producer.produce_triples(' '.join(article["texts"]))]
            self.db_article_collection.update_one({"source": article["source"]}, {"$set": {"triples": triples}})

            # check for conflict
            conflicted_triples = []
            for triple in triples:
                conflicts = self.knowledge_graph.get_triples(triple["subject"], triple["relation"])
                if conflicts is not None:
                    for conflict in conflicts:
                        del triple["added"]
                        conflicted_triples.append({"toBeInserted": triple, "inKnowledgeGraph": conflict.to_dict()})
            print(conflicted_triples)
            if len(conflicted_triples) > 0:
                self.db_article_collection.update_one({"source": article["source"]},
                                                      {"$set": {"conflicts": conflicted_triples}})

            if self.auto_update:
                # self.insert_all_nonconflicting_knowledge(triples,
                #                                          [conflict["toBeInserted"] for conflict in conflicted_triples])
                self.insert_all_nonconflicting_knowledge(article["source"])

    def insert_all_nonconflicting_knowledge(self, article_url):
        """
        Insert non-conflicting triples to the knowledge graph.
        :param triples: list of triples (in form of dictionaries) to be inserted
        :type triples: list
        :param conflicts: list of conflicted triples
        :type conflicts: list
        """
        article = self.db_article_collection.find_one({"source": article_url})
        conflicts = [conflict["toBeInserted"] for conflict in article["conflicts"]]
        for triple in article["triples"]:
            del triple["added"]
            if triple not in conflicts:
                self.knowledge_graph.insert_triple_object(Triple.from_dict(triple))
                triple["added"] = True
            else:
                triple["added"] = False
        self.db_article_collection.update_one({"source": article["source"]}, {"$set": {"triples": article["triples"]}})

    def delete_all_knowledge_from_article(self, article_url):
        """
        Delete triples that are extracted from an article, from the knowledge graph.
        Triples from the articles must have been extracted beforehand and stored in DB.
        :param article_url: URL of the article source
        :type article_url: str
        """
        article = self.db_article_collection.find_one({"source": article_url})
        if article["triples"] is not None:
            self.delete_knowledge(article["triples"])

    def delete_knowledge(self, triples):
        """
        Remove triples from knowledge graph.
        :param triples: list of triples (in form of dictionaries)
        """
        for triple in triples:
            self.knowledge_graph.delete_triple_object(Triple.from_dict(triple))
            self.db_article_collection.update_many({'triples': {'$elemMatch': {'subject': triple['subject'],
                                                                               'relation': triple['relation'],
                                                                               'objects': triple['objects']}}},
                                                   {'$set': {'triples.$.added': False}}
                                                   )
            self.db_triples_collection.update_one({'subject': triple['subject'],
                                                   'relation': triple['relation'],
                                                   'objects': triple['objects']},
                                                  {'$set': {'added': False}})


    def get_all_pending_knowledge(self):
        articles = []
        for article in self.db_article_collection.find({"triples": {"$exists": True}}):
            articles.append({
                "source": article["source"],
                "triples": [triple for triple in article["triples"] if triple["added"] is False]
            })
        return articles

    def insert_articles_knowledge(self, articles_triples):
        for article in articles_triples:
            print(article['source'])
            stored_triples = self.db_article_collection.find_one({'source': article['source']})['triples']
            for triple in article['triples']:

                self.knowledge_graph.insert_triple_object(Triple.from_dict(triple))
                if triple in stored_triples:
                    self.db_article_collection.update_one({'source': article['source'],
                                                           'triples': {'$elemMatch': {'subject': triple['subject'],
                                                                                      'relation': triple['relation'],
                                                                                      'objects': triple['objects']}}},
                                                          {'$set': {'triples.$.added': True}}
                                                          )
                else:
                    # accommodate triples about the article that are manually inserted
                    self.db_article_collection.update_one({'source': article['source']},
                                                          {'$push': {'triples': {
                                                              {'subject': triple['subject'],
                                                               'relation': triple['relation'],
                                                               'objects': triple['objects'],
                                                               'added': True}
                                                          }}})

    def insert_knowledge(self, triple, check_conflict):
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

    # TODO: delete knowledge

    # TODO: get entity
    def get_entity(self, subject):
        return self.knowledge_graph.get_entity('http://dbpedia.org/resource/' + subject)


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
