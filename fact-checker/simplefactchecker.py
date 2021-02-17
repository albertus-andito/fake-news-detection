from factchecker import FactChecker


class SimpleFactChecker(FactChecker):

    def fact_check(self, article):
        article_triples = self.get_triples(article)
        fc_result = [(sentence, {triple: self.knowledge_graph.check_triple_object_existence(triple)
                      for triple in triples}) for (sentence, triples) in article_triples]
        truth_values = [val for sentence, triples in fc_result for val in triples.values()]
        truthfulness = sum(truth_values) / len(truth_values)
        return fc_result, truthfulness

    def fact_check_triples(self, triples):
        fc_result = {triple: self.knowledge_graph.check_triple_object_existence(triple) for triple in triples}
        truthfulness = sum(fc_result.values()) / len(fc_result) if len(fc_result) > 0 else 0
        # what to return here?
        return fc_result, truthfulness

import pprint
if __name__ == '__main__':
    fc = SimpleFactChecker()
    text = 'Mr Giuliani ignored social distancing. He also claimed electoral fraud. He studied sociology.'
    triples = fc.get_triples(text)
    pprint.pprint(triples)
    print(type(triples[0]))

    pprint.pprint(fc.fact_check(text))