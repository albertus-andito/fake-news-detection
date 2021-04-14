from abc import ABC, abstractmethod

from common.kgwrapper import KnowledgeGraphWrapper
from common.tripleproducer import TripleProducer


class FactChecker(ABC):
    """
    Abstract class of a Fact Checker.
    """
    def __init__(self):
        self.triple_producer = TripleProducer(extractor_type='stanford_openie', extraction_scope='noun_phrases')
        self.knowledge_graph = KnowledgeGraphWrapper()

    @abstractmethod
    def fact_check(self, article, extraction_scope):
        """
        Abstract method of fact-checking.

        :param article: article text
        :type article: str
        :param extraction_scope: The scope of the extraction, deciding whether it should include only relations between
            'named_entities', 'noun_phrases', or 'all'.
        :type extraction_scope: str
        :return: a list of fact check result (sentence, {triples: their results})
        :rtype: list
        """
        pass

