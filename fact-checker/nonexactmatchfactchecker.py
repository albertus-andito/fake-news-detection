from nltk.corpus import wordnet as wn

from entitycorefresolver import EntityCorefResolver
from factchecker import FactChecker
from triple import Triple
from utils import convert_to_dbpedia_ontology


class NonExactMatchFactChecker(FactChecker):
    """
    A Non Exact Match Fact Checker.
    It considers the opposite relation (Object-Relation-Triple) of every triple.
    It also considers the synonyms of the relation, at the moment using WordNet.
    """

    def __init__(self):
        super().__init__()
        self.coref_resolver = EntityCorefResolver()

    def fact_check(self, article, extraction_scope):
        """
        Fact check the given text, by first extracting the triples and then infer the existence of the triples in the
        knowledge graph.
        The inference is done by finding the exact match, finding the triples of the opposite relation (Object - Relation
        - Subject), finding the triples where subject or object are corefering entities, and finding the triples with
        similar (based on synonymy) relations.
        Truthfulness score is calculated by dividing the number of inferred triples found by the number of all triples.
        :param article: article text
        :type article: str
        :param extraction_scope: The scope of the extraction, deciding whether it should include only relations between
        'named_entities', 'noun_phrases', or 'all'.
        :type extraction_scope: str
        :return: a tuple of fact check result (sentence, triples, and their existence) and the truthfulness score
        :rtype: tuple
        """
        article_triples = self.get_triples(article, extraction_scope)
        entity_clusters = self.coref_resolver.get_coref_clusters(article)
        # fc_result = [(sentence, {result[0]: result[1] for result in self.non_exact_fact_check(triple, entity_clusters)})
        #              for (sentence, triples) in article_triples for triple in triples]
        fc_result = [(sentence, {triple: self.non_exact_fact_check(triple, entity_clusters)
                                 for triple in triples}) for (sentence, triples) in article_triples]
        # truth_values = [sum(triples.values()) for sentence, triples in fc_result]
        # truthfulness = sum(truth_values) / len(truth_values)
        return fc_result

    def fact_check_triples(self, triples):
        """
        Fact check the given triples, by by first extracting the triples and then infer the existence of the triples in the
        knowledge graph.
        The inference is done by finding the exact match, finding the triples of the opposite relation (Object - Relation
        - Subject), and finding the triples with
        similar (based on synonymy) relations.
        Truthfulness score is calculated by dividing the number of inferred triples found by the number of all triples.
        :param triples: list of triples of type triple.Triple
        :type triples: list
        :return: a tuple of fact check result (triples and their existence) and the truthfulness score
        :rtype: tuple
        """
        # fc_result = [{result[0]: result[1] for result in self.non_exact_fact_check(triple)}
        #              for triple in triples]
        fc_result = {triple: self.non_exact_fact_check(triple) for triple in triples}
        # truth_values = [sum(triples.values()) for triples in fc_result]
        # truthfulness = sum(truth_values) / len(truth_values) if len(fc_result) > 0 else 0
        return fc_result

    def non_exact_fact_check(self, original_triple, entity_clusters=[]):
        """
        Check whether the triple or the "related triples" exist in the knowledge graph or not.
        Related triples are:
        - triples with the opposite relation (Object - Relationn - Subject)
        - triples with subject or object replaced with the corefering entity (if entity_clusters is not None)
        - triples with relation replaced with its synonyms
        :param original_triple: triple extracted from the text or inputted
        :type original_triple: triple.Triple
        :param entity_clusters: dictionary of entity coreference clusters
        :type entity_clusters: dict
        :return: a tuple of the triple and its existence, if found in the knowledge graph. None, otherwise.
        :rtype: tuple
        """
        original_exists = self.knowledge_graph.check_triple_object_existence(original_triple, transitive=True)
        if original_exists is True:
            return 'exists', []
        conflicts = self.knowledge_graph.get_triples(original_triple.subject, original_triple.relation)
        if conflicts is not None:
            return 'conflicts', conflicts

        triples = [original_triple]
        if len(entity_clusters) > 0:
            triples = self.__create_triples_from_coreference(original_triple, entity_clusters)

        possibilities = []
        for triple in triples:
            # check original triple
            original_exists = self.knowledge_graph.check_triple_object_existence(triple, transitive=True)
            if original_exists is True:
                possibilities.append(triple)
                break
            conflicts = self.knowledge_graph.get_triples(triple.subject, triple.relation, transitive=True)
            if conflicts is not None:
                return 'conflicts', conflicts
            # check triple with opposite relation (Object - Relation - Subject)
            opposite_exists = self.knowledge_graph.check_triple_object_opposite_relation_existence(triple, transitive=True)
            opposite_triple = [Triple(obj, triple.relation, [triple.subject]) for obj in triple.objects]
            if opposite_exists is True:
                possibilities.extend(opposite_triple)
            # check triple with the synonyms of its relation
            synonym_result = self.check_relation_synonyms(triple)
            if synonym_result is not None:
                possibilities.extend(synonym_result)
        if len(possibilities) > 0:
            return 'possible', possibilities

        return 'none', []

    def __create_triples_from_coreference(self, triple, entity_clusters):
        triples = [triple]
        # get corefering mentions of subject and objects
        corefs_subject = entity_clusters.get(triple.subject)
        corefs_objects = [entity_clusters.get(obj) for obj in triple.objects]
        corefs_objects = list(filter(None, corefs_objects))

        # extend triples with the combination of corefering mentions of subject and objects
        if corefs_subject is not None:
            triples.extend(
                [Triple(coref, triple.relation, triple.objects) for coref in corefs_subject])
        if len(corefs_objects) > 0:
            triples.extend(
                [Triple(triple.subject, triple.relation, [coref]) for obj in corefs_objects
                 for coref in obj])
        if corefs_subject is not None and len(corefs_objects) > 0:
            for coref_s in corefs_subject:
                for obj in corefs_objects:
                    triples.extend([Triple(coref_s, triple.relation, coref_o) for coref_o in obj])

        return triples

    def check_relation_synonyms(self, triple):
        """
        Check the existence of triples, in which the relation is a synonym of the relation of the inputted triple.
        Once a triple is found, it is returned without checking the other synonyms.
        Note that it also checks the opposite relation (Object - Relation - Subject).
        :param triple: triple of type triple.Triple
        :type triple: triple.Triple
        :return: the triple, if found in the knowledge graph. None, otherwise.
        :rtype: tuple
        """
        relation = triple.relation.replace('http://dbpedia.org/ontology/', '')
        synsets = wn.synsets(relation, pos=wn.VERB)
        for synset in synsets:
            for lemma in synset.lemmas():
                if lemma.name() != relation:
                    dbpedia_lemma = convert_to_dbpedia_ontology(lemma.name())
                    synonym_triple = Triple(triple.subject, dbpedia_lemma, triple.objects)
                    exists = self.knowledge_graph.check_triple_object_existence(synonym_triple, transitive=True)
                    if exists:
                        return [synonym_triple]
                    opposite_exists = self.knowledge_graph.check_triple_object_opposite_relation_existence(
                        synonym_triple, transitive=True)
                    if opposite_exists:
                        return [Triple(obj, dbpedia_lemma, [triple.subject]) for obj in triple.objects]


import pprint

# if __name__ == '__main__':
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

    # synsets = (wn.synsets('neglect', pos=wn.VERB))
    # print(synsets)
    # for synset in synsets:
    #     print('LEMMAS:')
    #     for lemma in synset.lemmas():
    #         print(lemma.name())
        # print('HYPERNYMS:')
        # for hypernym in synset.hypernyms():
        #     print(hypernym.name())
        # print('HYPONYMS:')
        # for hyponym in synset.hyponyms():
        #     print(hyponym.name())