from factchecker import FactChecker


class SimpleFactChecker(FactChecker):

    def fact_check(self, article):
        article_triples = self.get_triples(article)
        return self.fact_check_triples(article_triples)

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