from nltk.corpus import wordnet as wn

from factchecker import FactChecker
from triple import Triple


class BetterFactChecker(FactChecker):
    """
    A Better Fact Checker, compared to the Simple Fact Checker.
    It considers the opposite relation (Object-Relation-Triple) of every triple.
    It also considers the synonyms of the relation, at the moment using WordNet.
    """
    def fact_check(self, article):
        article_triples = self.get_triples(article)
        fc_result = [(sentence, {result[0]: result[1] for result in self.better_fact_check(triple)})
                     for (sentence, triples) in article_triples for triple in triples]
        truth_values = [sum(triples.values()) for sentence, triples in fc_result]
        truthfulness = sum(truth_values) / len(truth_values)
        return fc_result, truthfulness

    def fact_check_triples(self, triples):
        fc_result = [{result[0]: result[1] for result in self.better_fact_check(triple)}
                     for triple in triples]
        truth_values = [sum(triples.values()) for triples in fc_result]
        truthfulness = sum(truth_values) / len(truth_values) if len(fc_result) > 0 else 0
        return fc_result, truthfulness

    def better_fact_check(self, triple):
        # check original triple
        original = self.knowledge_graph.check_triple_object_existence(triple, transitive=True)
        if original is True:
            return [(triple, original)]
        # check triple with opposite relation (Object - Relation - Subject)
        opposite = self.knowledge_graph.check_triple_object_opposite_relation_existence(triple, transitive=True)
        opposite_triple = Triple(triple.subject, 'is ' + triple.relation + ' of', triple.objects)
        if opposite is True:
            return [(opposite_triple, opposite)]
        # check triple with the synonyms of its relation
        synonym_result = self.check_relation_synonyms(triple)
        if synonym_result is not None:
            return [(triple, original), (opposite_triple, opposite), synonym_result]

        return [(triple, original), (opposite_triple, opposite)]

    def check_relation_synonyms(self, triple):
        """
        Check the existence of triples, in which the relation is a synonym of the relation of the inputted triple.
        Once a triple is found, it is returned without checking the other synonyms.
        Note that it also checks the opposite relation (Object - Relation - Subject).
        :param triple: triple of type triple.Triple
        :type triple: triple.Triple
        :return: a tuple of the triple and its existence, if found in the knowledge graph. None, otherwise.
        :rtype: tuple
        """
        relation = triple.relation.replace('http://dbpedia.org/ontology/', '')
        synsets = wn.synsets(relation, pos=wn.VERB)
        for synset in synsets:
            for lemma in synset.lemmas():
                dbpedia_lemma = 'http://dbpedia.org/ontology/' + lemma.name()
                synonym_triple = Triple(triple.subject, dbpedia_lemma, triple.objects)
                exists = self.knowledge_graph.check_triple_object_existence(synonym_triple, transitive=True)
                if exists:
                    return synonym_triple, exists
                opposite_exists = self.knowledge_graph.check_triple_object_opposite_relation_existence(synonym_triple,
                                                                                                       transitive=True)
                if opposite_exists:
                    return Triple(triple.subject, 'is ' + dbpedia_lemma + ' of', triple.objects), opposite_exists

import pprint

if __name__ == '__main__':
    # fc = BetterFactChecker()
    # triple = Triple("http://dbpedia.org/resource/Social_distancing", "http://dbpedia.org/ontology/ignore",
    #                 ["http://dbpedia.org/resource/Mr_Giuliani"])
    # res = fc.fact_check_triples([triple])
    # pprint.pprint(res)

    # text = 'Mr Giuliani ignored social distancing. He also claimed electoral fraud. He studied sociology.'
    # text = 'Social distancing was ignored by Mr Giuliani. He also claimed electoral fraud. He studied sociology. ' \
    #        'He was admitted to hospital on Sunday.'
    # pprint.pprint(fc.fact_check(text))
    # a_dict = {'a': True, 'b': True}
    # print(sum(a_dict.values()))
    # print(all([]))

    synsets = (wn.synsets('neglect', pos=wn.VERB))
    print(synsets)
    for synset in synsets:
        print('LEMMAS:')
        for lemma in synset.lemmas():
            print(lemma.name())
        print('HYPERNYMS:')
        for hypernym in synset.hypernyms():
            print(hypernym.name())
        print('HYPONYMS:')
        for hyponym in synset.hyponyms():
            print(hyponym.name())
