from nltk import word_tokenize

DBPEDIA_RESOURCE = "http://dbpedia.org/resource/"
DBPEDIA_ONTOLOGY = "http://dbpedia.org/ontology/"

def camelise(sentence):
    """
    Util function to convert words into camelCase

    :param sentence: sentence
    :type sentence: str
    :return: camelCase words
    :rtype: str
    """
    sentence = sentence.replace('_', ' ')
    words = word_tokenize(sentence)
    if len(words) <= 1:
        return sentence.lower()
    else:
        s = "".join(word[0].upper() + word[1:].lower() for word in words)
        return s[0].lower() + s[1:]


def convert_to_dbpedia_resource(resource):
    """
    Converts a resource string to a DBpedia format (http://dbpedia.org/resource/).

    :param resource: resource string
    :type resource: str
    :return: DBpedia resource string
    :rtype: str
    """
    if resource.startswith(DBPEDIA_RESOURCE):
        return resource
    return DBPEDIA_RESOURCE + resource.replace(' ', '_')


def convert_to_dbpedia_ontology(predicate):
    """
        Converts a relation or predicate string to a DBpedia format (http://dbpedia.org/ontology/).

        :param predicate: relation string
        :type predicate: str
        :return: DBpedia ontology string
        :rtype: str
        """
    return DBPEDIA_ONTOLOGY + camelise(predicate).lstrip()
