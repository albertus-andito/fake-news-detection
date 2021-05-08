import unittest

from ..utils import camelise, convert_to_dbpedia_ontology, convert_to_dbpedia_resource


class TestUtils(unittest.TestCase):

    def test_camelise(self):
        self.assertEqual("helloWorld", camelise("hello world"))
        self.assertEqual("helloWorld", camelise("hello_world"))
        self.assertEqual("helloWorld", camelise("Hello World"))
        self.assertEqual("helloWorld", camelise("HELLO WORLD"))

    def test_convert_to_resource(self):
        self.assertEqual("http://dbpedia.org/resource/John_Doe", convert_to_dbpedia_resource("John Doe"))

    def test_convert_to_ontology(self):
        self.assertEqual("http://dbpedia.org/ontology/ignoreAgain", convert_to_dbpedia_ontology("ignore again"))


if __name__ == '__main__':
    unittest.main()
