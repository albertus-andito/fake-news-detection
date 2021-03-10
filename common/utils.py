from nltk import word_tokenize


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
    return 'http://dbpedia.org/resource/' + resource.replace(' ', '_')


def convert_to_dbpedia_ontology(predicate):
    return 'http://dbpedia.org/ontology/' + camelise(predicate).lstrip()
