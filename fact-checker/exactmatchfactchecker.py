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
        fc_result = [(sentence, {triple: self.exact_fact_check(triple)
                      for triple in triples}) for (sentence, triples) in article_triples]
        # truth_values = [val for sentence, triples in fc_result for val in triples.values()]
        # truthfulness = sum(truth_values) / len(truth_values) if len(fc_result) > 0 else 0
        return fc_result

    def fact_check_triples(self, triples, transitive=False):
        """
        Fact check the given triples, by finding the exact match of the triples in the knowledge graph.
        Truthfulness score is calculated simply by dividing the number of triples found by the number of all triples.
        :param triples: list of triples of type triple.Triple
        :type triples: list
        :param transitive: whether a check should also be done for entities that are in the sameAs relation with the subject
        :type transitive: bool
        :return: a tuple of fact check result (triples and their existence) and the truthfulness score
        :rtype: tuple
        """
        fc_result = {triple: self.exact_fact_check(triple, transitive) for triple in triples}
        # truthfulness = sum(fc_result.values()) / len(fc_result) if len(fc_result) > 0 else 0
        # what to return here?
        return fc_result

    def exact_fact_check(self, triple, transitive=False):
        """
        Checks for the triple existence and conflicts
        :param triple: triple to be checked
        :type triple: triple.Triple
        :param transitive: whether a check should also be done for entities that are in the sameAs relation with the subject
        :type transitive: bool
        :return: a tuple of its result and supporting triples
        :rtype: tuple
        """
        exists = self.knowledge_graph.check_triple_object_existence(triple, transitive)
        if exists is True:
            return 'exists', []
        conflicts = self.knowledge_graph.get_triples(triple.subject, triple.relation, transitive)
        if conflicts is not None:
            return 'conflicts', conflicts
        # The following checks triples with the same subject and object, but different relation. Are those conflict?
        # if conflicts is None:
        #     conflicts = []
        # for obj in triple.objects:
        #     relations = self.knowledge_graph.get_relation_triples(triple.subject, obj)
        #     if relations is not None:
        #         conflicts += relations
        # if len(conflicts) > 0:
        #     return 'conflicts', conflicts
        return 'none', []

import pprint
if __name__ == '__main__':
    fc = ExactMatchFactChecker()
    text = 'Mr Giuliani ignored social distancing. He also claimed electoral fraud. He studied sociology.'
    triples = fc.get_triples(text)
    pprint.pprint(triples)
    print(type(triples[0]))

    pprint.pprint(fc.fact_check(text))