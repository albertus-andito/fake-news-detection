import responses
import spacy
import unittest

from mock import patch

from ..triple import Triple
from ..tripleproducer import TripleProducer


class TestTripleProducer(unittest.TestCase):

    text = "John Doe ignored social distancing."
    nlp = spacy.load('en_core_web_sm')

    @patch('common.tripleproducer.StanfordExtractor')
    def test_extract_triples(self, mock_stanford):
        triple_1 = Triple("John Doe", "ignored", ["distancing"])
        triple_2 = Triple("John Doe", "ignored", ["social distancing"])
        triples = [triple_1, triple_2]
        mock_stanford.return_value.extract.return_value = triples

        producer = TripleProducer()
        extracted_triples = producer.extract_triples([self.text])

        self.assertEqual([triples], extracted_triples)

    @patch('common.tripleproducer.StanfordExtractor')
    def test_remove_stopwords(self, mock_stanford):
        with_stopword = Triple("John Doe", "ignored", ["the distancing"])
        without_stopword = Triple("John Doe", "ignored", ["distancing"])

        producer = TripleProducer()
        result = producer.remove_stopwords([[with_stopword]])

        self.assertEqual([[without_stopword]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    def test_filter_in_named_entities(self, mock_stanford):
        triple_1 = Triple("John", "marries", ["Michelle"])
        triple_2 = Triple("John Doe", "ignored", ["social distancing"])

        doc = self.nlp("John marries Michelle. John Doe ignored social distancing.")
        producer = TripleProducer()
        result = producer.filter_in_named_entities(doc, [[triple_1, triple_2]])

        self.assertEqual([[triple_1]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    def test_filter_in_noun_phrases(self, mock_stanford):
        triple_1 = Triple("John Doe", "ignored", ["social distancing"])
        triple_2 = Triple("John", "walks", ["towards"])

        doc = self.nlp("John Doe ignored social distancing. John walks towards.")
        producer = TripleProducer()
        result = producer.filter_in_noun_phrases(doc, [[triple_1, triple_2]])

        self.assertEqual([[triple_1]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    def test_filter_noun_phrases(self, mock_stanford):
        triple_1 = Triple("John Doe", "ignored", ["social distancing"])
        triple_2 = Triple("John", "walks", ["towards"])

        producer = TripleProducer()
        result = producer.filter_noun_phrases([[triple_1, triple_2]])

        self.assertEqual([[triple_1]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    @responses.activate
    def test_spot_entities_with_context(self, mock_stanford):
        responses.add(responses.GET, 'https://api.dbpedia-spotlight.org/en/annotate?text=John+Doe+ignored+social+distancing.',
                      json={
                            "Resources": [
                                {
                                    "@URI": "http://dbpedia.org/resource/John_Doe",
                                    "@surfaceForm": "John Doe"
                                },
                                {
                                    "@URI": "http://dbpedia.org/resource/Social_distancing",
                                    "@surfaceForm": "social distancing"
                                },
                            ]
                      }, status=200)

        triple = Triple("John Doe", "ignored", ["social distancing"])
        spotted_triple = Triple("http://dbpedia.org/resource/John_Doe", "ignored", ["http://dbpedia.org/resource/Social_distancing"])

        producer = TripleProducer()
        result = producer.spot_entities_with_context(self.text, [[triple]])

        self.assertEqual([[spotted_triple]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    @patch('common.tripleproducer.KnowledgeGraphWrapper')
    def test_spot_local_entities_object_not_exist(self, mock_kg, mock_stanford):
        mock_kg.return_value.check_resource_existence.return_value = False

        triple = Triple("John Doe", "ignored", ["social distancing"])
        spotted_triple = Triple("http://dbpedia.org/resource/John_Doe", "ignored", ["social distancing"])

        producer = TripleProducer()
        result = producer.spot_local_entities([[triple]])

        self.assertEqual([[spotted_triple]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    @patch('common.tripleproducer.KnowledgeGraphWrapper')
    def test_spot_local_entities_object_exist(self, mock_kg, mock_stanford):
        mock_kg.return_value.check_resource_existence.return_value = True

        triple = Triple("John Doe", "ignored", ["social distancing"])
        spotted_triple = Triple("http://dbpedia.org/resource/John_Doe", "ignored",
                                ["http://dbpedia.org/resource/social_distancing"])

        producer = TripleProducer()
        result = producer.spot_local_entities([[triple]])

        self.assertEqual([[spotted_triple]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    @responses.activate
    def test_link_relation_falcon(self, mock_stanford):
        text = "Barrack Obama was born in Hawaii."
        responses.add(responses.POST,
                      'https://labs.tib.eu/falcon/api?mode=long',
                      match=[
                          responses.json_params_matcher({'text': text})
                      ],
                      json={
                          "entities": [
                            [
                                "http://dbpedia.org/resource/Barack_Obama",
                                "Barrack obama"
                            ],
                            [
                                "http://dbpedia.org/resource/Hawaii",
                                "Hawaii"
                            ]
                          ],
                          "relations": [
                            [
                            "http://dbpedia.org/ontology/birthPlace",
                            "born"
                            ]
                          ]
                      }, status=200)
        triple = Triple("http://dbpedia.org/resource/Barack_Obama", "born in", ["http://dbpedia.org/resource/Hawaii"])
        linked_triple = Triple("http://dbpedia.org/resource/Barack_Obama", "http://dbpedia.org/ontology/birthPlace", ["http://dbpedia.org/resource/Hawaii"])

        producer = TripleProducer()
        result = producer.link_relations([text], [[triple]])

        self.assertEqual([[linked_triple]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    def test_lemmatise_relation(self, mock_stanford):
        triple = Triple("John Doe", "ignored", ["social distancing"])
        lemmatised_triple = Triple("John Doe", "ignore", ["social distancing"])

        doc = self.nlp(self.text)
        producer = TripleProducer()
        result = producer.lemmatise_relations(doc, [[triple]])

        self.assertEqual([[lemmatised_triple]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    def test_convert_relations(self, mock_stanford):
        triple = Triple("John Doe", "ignore", ["social distancing"])
        converted_triple = Triple("John Doe", "http://dbpedia.org/ontology/ignore", ["social distancing"])

        producer = TripleProducer()
        result = producer.convert_relations([[triple]])

        self.assertEqual([[converted_triple]], result)

    @patch('common.tripleproducer.StanfordExtractor')
    def test_remove_empty(self, mock_stanford):
        empty_subject = Triple("", "ignore", ["social distancing"])
        empty_relation = Triple("John Doe", "", ["social distancing"])
        empty_object = Triple("John Doe", "ignore", [""])

        producer = TripleProducer()

        self.assertEqual([[]], producer.remove_empty_components([[empty_subject]]))
        self.assertEqual([[]], producer.remove_empty_components([[empty_relation]]))
        self.assertEqual([[]], producer.remove_empty_components([[empty_object]]))


if __name__ == '__main__':
    unittest.main()
