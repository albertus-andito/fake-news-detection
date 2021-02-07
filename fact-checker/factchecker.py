from abc import ABC, abstractmethod

from kgwrapper import KnowledgeGraphWrapper
from tripleproducer import TripleProducer


class FactChecker(ABC):

    def __init__(self):
        self.triple_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
        self.knowledge_graph = KnowledgeGraphWrapper()

    @abstractmethod
    def fact_check(self, article):
        pass

    def get_triples(self, article):
        return self.triple_producer.produce_triples(article)

