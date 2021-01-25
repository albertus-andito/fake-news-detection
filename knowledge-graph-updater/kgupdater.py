import bson
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
        self.db_collection = self.db["articles"]
        self.db_collection.create_index("source", unique=True)

        self.triple_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
        self.knowledge_graph = KnowledgeGraphWrapper()
        if auto_update is None:
            self.auto_update = True
        else:
            self.auto_update = auto_update

    def update_missed_knowledge(self):
        """
        Extract triples from stored articles whose triples has not been extracted yet, and save the triples to the DB.
        Triples that have conflicts in the knowledge graph are identified.
        If the auto_update mode is active, the triples are added to the knowledge graph.
        """
        for article in self.db_collection.find({"triples": None}):
            print(' '.join(article["texts"]))
            triples = [triple.to_dict() for triple in self.triple_producer.produce_triples(' '.join(article["texts"]))]
            self.db_collection.update_one({"source": article["source"]}, {"$set": {"triples": triples}})

            # check for conflict
            conflicted_triples = []
            for triple in triples:
                conflicts = self.knowledge_graph.get_triples(triple["subject"], triple["relation"])
                if conflicts is not None:
                    for conflict in conflicts:
                        conflicted_triples.append({"toBeInserted": triple, "inKnowledgeGraph": conflict.to_dict()})
            print(conflicted_triples)
            if len(conflicted_triples) > 0:
                self.db_collection.update_one({"source": article["source"]},
                                              {"$set": {"conflicts": conflicted_triples}})

            if self.auto_update:
                self.insert_all_nonconflicting_knowledge(triples,
                                                         [conflict["toBeInserted"] for conflict in conflicted_triples])

    def insert_all_nonconflicting_knowledge(self, triples, conflicts):
        """
        Insert non-conflicting triples to the knowledge graph.
        :param triples: list of triples (in form of dictionaries) to be inserted
        :type triples: list
        :param conflicts: list of conflicted triples
        :type conflicts: list
        """
        for triple in triples:
            if triple not in conflicts:
                self.knowledge_graph.insert_triple_object(Triple.from_dict(triple))

    def delete_knowledge_from_article(self, article_url):
        """
        Delete triples that are extracted from an article, from the knowledge graph.
        Triples from the articles must have been extracted beforehand and stored in DB.
        :param article_url: URL of the article source
        :type article_url: str
        """
        article = self.db_collection.find_one({"source": article_url})
        if article["triples"] is not None:
            self.delete_knowledge(article["triples"])

    def delete_knowledge(self, triples):
        """
        Remove triples from knowledge graph.
        :param triples: list of triples (in form of dictionaries)
        """
        for triple in triples:
            self.knowledge_graph.delete_triple_object(Triple.from_dict(triple))


if __name__ == '__main__':
    kgu = KnowledgeGraphUpdater()
    kgu.update_missed_knowledge()
    kgu.delete_knowledge_from_article("https://www.bbc.co.uk/news/world-us-canada-55210243")
