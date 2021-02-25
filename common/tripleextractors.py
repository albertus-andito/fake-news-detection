import json
import logging
import logging.config
import os
from abc import ABC, abstractmethod
from json import JSONDecodeError

from dotenv import load_dotenv
from pathlib import Path
from pyopenie import OpenIE5
from stanfordcorenlp import StanfordCoreNLP

from definitions import ROOT_DIR, LOGGER_CONFIG_PATH
from triple import Triple


class TripleExtractor(ABC):
    """
    Abstract class of Triple Extractor
    """
    def __init__(self):
        LOGFILE_PATH = os.path.join(ROOT_DIR, 'logs', 'triple-extractor.log').replace("\\", "/")
        logging.config.fileConfig(LOGGER_CONFIG_PATH,
                                  defaults={'logfilename': LOGFILE_PATH},
                                  disable_existing_loggers=False)
        self.logger = logging.getLogger()
    
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
        super(StanfordExtractor, self).__init__()
        load_dotenv(dotenv_path=Path('../.env'))
        self.coreNLP = StanfordCoreNLP(os.getenv('STANFORD_CORE_NLP_HOST'),
                                       port=int(os.getenv('STANFORD_CORE_NLP_PORT')))

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
        try:
            outputs = json.loads(self.coreNLP.annotate(document, self.props), encoding='utf-8')['sentences']
        except JSONDecodeError as e:
            self.logger.error('Triple extraction error: JSONDecodeError ' + e.__str__())
            return []
        all_triples = [Triple(openie_triple['subject'], openie_triple['relation'], [openie_triple['object']])
                       for output in outputs for openie_triple in output['openie']]
        return all_triples


class IITExtractor(TripleExtractor):
    """
    Triple extraction using IIT OpenIE (https://github.com/vaibhavad/python-wrapper-OpenIE5)
    """
    def __init__(self):
        super(IITExtractor, self).__init__()
        load_dotenv(dotenv_path=Path('../.env'))
        self.openie = OpenIE5(os.getenv("IIT_OPENIE_URL"))

    def extract(self, document):
        """
        Extract SPO triples from document
        :param document: document
        :type document: str
        :return: list of triples
        :rtype: list
        """
        extractions = self.openie.extract(document)
        all_triples = [Triple(extraction['extraction']['arg1']['text'], extraction['extraction']['rel']['text'],
                              [obj['text'] for obj in extraction['extraction']['arg2s']])
                       for extraction in extractions]
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
