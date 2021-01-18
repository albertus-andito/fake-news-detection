import json
import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from pathlib import Path
from pyopenie import OpenIE5
from stanfordcorenlp import StanfordCoreNLP


class TripleExtractor(ABC):
    """
    Abstract class of Triple Extractor
    """
    @abstractmethod
    def extract(self, document):
        """
        Extract SPO triples from document
        :param document: document
        :type document: str
        :return: list of triples
        :rtype: list
        """
        pass


class StanfordExtractor(TripleExtractor):
    """
    Triple extraction using Stanford OpenIE (https://github.com/Lynten/stanford-corenlp)
    """
    props = {'annotators': 'openie', 'pipelineLanguage': 'en', 'outputFormat': 'json'}

    def __init__(self):
        load_dotenv(dotenv_path=Path('./.env'))
        self.coreNLP = StanfordCoreNLP(os.getenv("STANFORD_CORE_NLP_PATH"))

    def __del__(self):
        self.coreNLP.close()

    def extract(self, document):
        """
        Extract SPO triples from document
        :param document: document
        :type document: str
        :return: list of triples
        :rtype: list
        """
        output_sentences = json.loads(self.coreNLP.annotate(document, self.props), encoding='utf-8')['sentences']
        all_triples = []
        for sentence in output_sentences:
            openie = sentence['openie']
            for openie_triple in openie:
                triple = {
                    "subject": openie_triple['subject'],
                    "relation": openie_triple['relation'],
                    "object": [openie_triple['object']]
                }
                all_triples.append(triple)
        return all_triples


class IITExtractor(TripleExtractor):
    """
    Triple extraction using IIT OpenIE (https://github.com/vaibhavad/python-wrapper-OpenIE5)
    """
    def __init__(self):
        load_dotenv(dotenv_path=Path('./.env'))
        self.openie = OpenIE5(os.getenv("IIT_OPENIE_URL"))

    def extract(self, document):
        """
        Extract SPO triples from document
        :param document: document
        :type document: str
        :return: list of triples
        :rtype: list
        """
        all_triples = []
        extractions = self.openie.extract(document)
        for extraction in extractions:
            spo = {
                "subject": extraction['extraction']['arg1']['text'],
                "relation": extraction['extraction']['rel']['text'],
                "object": [obj['text'] for obj in extraction['extraction']['arg2s']]
            }
            all_triples.append(spo)
        return all_triples

# Testing
import pprint
if __name__ == '__main__':
    stanford = StanfordExtractor()
    iit = IITExtractor()

    doc = "Stores and supermarkets in Veracruz (Mexico) will close due to the new coronavirus. The local government " \
          "has asked people to buy supplies. "
    stanford_triples = stanford.extract(doc)
    pprint.pprint(stanford_triples)

    iit_triples = iit.extract(doc)
    pprint.pprint(iit_triples)
