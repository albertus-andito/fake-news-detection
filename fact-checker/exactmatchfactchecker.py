from factchecker import FactChecker


class ExactMatchFactChecker(FactChecker):
    """
    An Exact Match Fact Checker, where a truthfulness is decided only by finding the exact match of the triples.
    """
    def fact_check(self, article):
        """
        Fact check the given text, by first extracting the triples and then finding the exact match of the triples in the
        knowledge graph.
        Truthfulness score is calculated simply by dividing the number of triples found by the number of all triples.
        :param article: article text
        :type article: str
        :return: a tuple of fact check result (sentence, triples, and their existence) and the truthfulness score
        :rtype: tuple
        """
        article_triples = self.get_triples(article)
        fc_result = [(sentence, {triple: self.knowledge_graph.check_triple_object_existence(triple)
                      for triple in triples}) for (sentence, triples) in article_triples]
        truth_values = [val for sentence, triples in fc_result for val in triples.values()]
        truthfulness = sum(truth_values) / len(truth_values)
        return fc_result, truthfulness

    def fact_check_triples(self, triples):
        """
        Fact check the given triples, by finding the exact match of the triples in the knowledge graph.
        Truthfulness score is calculated simply by dividing the number of triples found by the number of all triples.
        :param triples: list of triples of type triple.Triple
        :type triples: list
        :return: a tuple of fact check result (triples and their existence) and the truthfulness score
        :rtype: tuple
        """
        fc_result = {triple: self.knowledge_graph.check_triple_object_existence(triple) for triple in triples}
        truthfulness = sum(fc_result.values()) / len(fc_result) if len(fc_result) > 0 else 0
        # what to return here?
        return fc_result, truthfulness

import pprint
if __name__ == '__main__':
    fc = ExactMatchFactChecker()
    text = 'Mr Giuliani ignored social distancing. He also claimed electoral fraud. He studied sociology.'
    triples = fc.get_triples(text)
    pprint.pprint(triples)
    print(type(triples[0]))

    pprint.pprint(fc.fact_check(text))