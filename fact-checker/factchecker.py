from abc import ABC, abstractmethod

from kgwrapper import KnowledgeGraphWrapper
from tripleproducer import TripleProducer


class FactChecker(ABC):
    """
    Abstract class of a Fact Checker.
    """
    def __init__(self):
        self.triple_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
        self.knowledge_graph = KnowledgeGraphWrapper()

    @abstractmethod
    def fact_check(self, article):
        pass

    def get_triples(self, article, extraction_scope='noun_phrases'):
        """
        Extract triples from the given article text.
        :param article: article text
        :type article: str
        :param extraction_scope: The scope of the extraction, deciding whether it should include only relations between
        'named_entities', 'noun_phrases', or 'all', defaults to 'noun_phrases' for now.
        :type extraction_scope: str
        :return: a list of tuples, of sentence and its triples, as explained
        :rtype: list
        """
        return self.triple_producer.produce_triples(article, extraction_scope)

