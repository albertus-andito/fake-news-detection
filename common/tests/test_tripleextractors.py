import unittest
from mock import patch

from ..triple import Triple
from ..tripleextractors import StanfordExtractor


class TestTripleExtractors(unittest.TestCase):

    text = "John Doe ignored social distancing."
    stanford_result = '{"sentences": [{"openie":[' \
                      '{"subject": "John Doe", "relation": "ignored", "object": "distancing"},' \
                      '{"subject": "John Doe", "relation": "ignored", "object": "social distancing"}' \
                      ']}]}'

    @patch('common.tripleextractors.StanfordCoreNLP')
    def test_stanford_extractor(self, mock_stanford):
        mock_stanford.return_value.annotate.return_value = '{"sentences": [{"openie":[' \
                      '{"subject": "John Doe", "relation": "ignored", "object": "distancing"},' \
                      '{"subject": "John Doe", "relation": "ignored", "object": "social distancing"}' \
                      ']}]}'
        triple_1 = Triple("John Doe", "ignored", ["distancing"])
        triple_2 = Triple("John Doe", "ignored", ["social distancing"])

        extractor = StanfordExtractor()
        triples = extractor.extract(self.text)

        self.assertEqual(len(triples), 2)
        self.assertEqual(triple_1, triples[0])
        self.assertEqual(triple_2, triples[1])


if __name__ == '__main__':
    unittest.main()