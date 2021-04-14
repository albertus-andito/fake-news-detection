import neuralcoref
import spacy

from .utils import convert_to_dbpedia_resource


class EntityCorefResolver:
    """
    Entity Coreference Resolver (using Spacy and Neuralcoref)
    """
    BLACKLIST = ['i', 'me', 'my', 'mine',
                 'you', 'your', 'yours',
                 'he', 'him', 'his',
                 'she', 'her', 'hers',
                 'we', 'us', 'our', 'ours',
                 'they', 'them', 'their', 'theirs',
                 'it', 'its']

    def __init__(self):
        self.nlp = spacy.load('en')
        neuralcoref.add_to_pipe(self.nlp)

    def get_coref_clusters(self, doc):
        """
        Gets coreference clusters in DBpedia format.
        It returns a dictionary, where each key is the most representative mention for the cluster,
        and each value is a set of the other mentions for the cluster
        Standard pronouns (listed in BLACKLIST) are excluded.

        :param doc: a text
        :type doc: str
        :return: dictionary of coreference clusters, as described above
        :rtype: dict
        """
        spacy_doc = self.nlp(doc)
        coref_clusters = {convert_to_dbpedia_resource(cluster.main.text): {convert_to_dbpedia_resource(mention.text)
                                                                           for mention in cluster.mentions
                                                                           if mention.text.lower() not in self.BLACKLIST
                                                                           and mention.text != cluster.main.text}
                          for cluster in spacy_doc._.coref_clusters}
        coref_clusters = {main: mentions for main, mentions in coref_clusters.items() if len(mentions) > 0}
        return coref_clusters
