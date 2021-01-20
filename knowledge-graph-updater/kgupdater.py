import bson
import logging.config
import os
import pprint
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

from definitions import ROOT_DIR, LOGGER_CONFIG_PATH
from tripleproducer import TripleProducer


class KnowledgeGraphUpdater:

    def __init__(self):
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

        self.triple_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='all')

    def update_missed_knowledge(self):
        for article in self.db_collection.find({"triples": None}):
            print(' '.join(article["texts"]))
            triples = [triple.to_dict() for triple in self.triple_producer.produce_triples(' '.join(article["texts"]))]
            self.db_collection.update_one({"source": article["source"]}, {"$set": {"triples": triples}})


if __name__ == '__main__':
    kgu = KnowledgeGraphUpdater()
    kgu.update_missed_knowledge()
