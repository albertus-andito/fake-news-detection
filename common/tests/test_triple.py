import unittest

from ..triple import Triple
from ..utils import DBPEDIA_RESOURCE, DBPEDIA_ONTOLOGY


class TestTriple(unittest.TestCase):
    subject = DBPEDIA_RESOURCE + 'John_Doe'
    relation = DBPEDIA_ONTOLOGY + 'ignore'
    objects = [DBPEDIA_RESOURCE + 'Social_distancing']

    json_str = '{"subject": "http://dbpedia.org/resource/John_Doe", ' \
               '"relation": "http://dbpedia.org/ontology/ignore", ' \
               '"objects": ["http://dbpedia.org/resource/Social_distancing"]}'

    dic = {
        'subject': subject,
        'relation': relation,
        'objects': objects
    }

    def test_create_triple(self):

        triple = Triple(self.subject, self.relation, self.objects)
        self.assertEqual(self.subject, triple.subject)
        self.assertEqual(self.relation, triple.relation)
        self.assertEqual(self.objects, triple.objects)

    def test_create_triple_from_json(self):
        triple = Triple.from_json(self.json_str)
        self.assertEqual(self.subject, triple.subject)
        self.assertEqual(self.relation, triple.relation)
        self.assertEqual(self.objects, triple.objects)

    def test_to_json(self):
        triple = Triple(self.subject, self.relation, self.objects)
        self.assertEqual(self.json_str, triple.to_json())

    def test_create_triple_from_dict(self):
        triple = Triple.from_dict(self.dic)
        self.assertEqual(self.subject, triple.subject)
        self.assertEqual(self.relation, triple.relation)
        self.assertEqual(self.objects, triple.objects)

    def test_to_dict(self):
        triple = Triple(self.subject, self.relation, self.objects)
        self.assertEqual(self.dic, triple.to_dict())


if __name__ == '__main__':
    unittest.main()
