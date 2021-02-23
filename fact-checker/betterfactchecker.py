from factchecker import FactChecker
from triple import Triple


class BetterFactChecker(FactChecker):
    """
    A Better Fact Checker, compared to the Simple Fact Checker.
    It considers the opposite relation (Object-Relation-Triple) of every triple.
    """
    def fact_check(self, article):
        article_triples = self.get_triples(article)
        fc_result = [(sentence, {result[0]: result[1] for result in self.check_opposite_relations(triple)})
                     for (sentence, triples) in article_triples for triple in triples]
        truth_values = [sum(triples.values()) for sentence, triples in fc_result]
        truthfulness = sum(truth_values) / len(truth_values)
        return fc_result, truthfulness

    def fact_check_triples(self, triples):
        fc_result = [{result[0]: result[1] for result in self.check_opposite_relations(triple)}
                     for triple in triples]
        truth_values = [sum(triples.values()) for triples in fc_result]
        truthfulness = sum(truth_values) / len(truth_values) if len(fc_result) > 0 else 0
        return fc_result, truthfulness

    def check_opposite_relations(self, triple):
        original = self.knowledge_graph.check_triple_object_existence(triple)
        if original is True:
            return [(triple, original)]
        opposite = self.knowledge_graph.check_triple_object_opposite_relation_existence(triple)
        opposite_triple = Triple(triple.subject, 'is ' + triple.relation + ' of', triple.objects)
        if opposite is True:
            return [(opposite_triple, opposite)]
        return [(triple, original), (opposite_triple, opposite)]


import pprint

if __name__ == '__main__':
    fc = BetterFactChecker()
    triple = Triple("http://dbpedia.org/resource/Social_distancing", "http://dbpedia.org/ontology/ignore",
                    ["http://dbpedia.org/resource/Mr_Giuliani"])
    res = fc.fact_check_triples([triple])
    pprint.pprint(res)

    # text = 'Mr Giuliani ignored social distancing. He also claimed electoral fraud. He studied sociology.'
    # text = 'Social distancing was ignored by Mr Giuliani. He also claimed electoral fraud. He studied sociology. ' \
    #        'He was admitted to hospital on Sunday.'
    # pprint.pprint(fc.fact_check(text))
    # a_dict = {'a': True, 'b': True}
    # print(sum(a_dict.values()))
    # print(all([]))
