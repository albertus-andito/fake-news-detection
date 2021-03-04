import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from triple import Triple
import pprint


class KnowledgeGraphWrapper:
    """
    A wrapper for RDF Triple Store (Knowledge Graph) operations.
    """

    def __init__(self):
        """
        Constructor method
        """
        load_dotenv(dotenv_path=Path('../.env'))
        self.sparql = SPARQLWrapper(os.getenv("SPARQL_ENDPOINT"))
        self.logger = logging.getLogger()

    def check_resource_existence(self, resource):
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                ASK WHERE {{
                  {{ <{0}> ?p ?o . }}
                  UNION
                  {{ ?s ?p <{0}> . }}
                }}
                """.format(resource)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Checking resource existence: %s", resource)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Check resource existence failed with status code " + results.responses.status)
        return results.convert()["boolean"]

    def check_triple_object_existence(self, triple, transitive=False):
        """
        Checks if a triple exists or not in the knowledge graph
        :param triple: a triple of type triple.Triple
        :type triple: triple.Triple
        :param transitive: whether a check should also be done for entities that are in the sameAs relation with the subject
        :type transitive: bool
        :return: True if triple exists, False otherwise
        :rtype: bool
        """
        exists = [self.check_triple_existence(triple.subject, triple.relation, obj, transitive) for obj in triple.objects]
        return all(exists)

    def check_triple_object_opposite_relation_existence(self, triple, transitive=False):
        """
        Checks if a triple with the opposite relation (Objects-Relation-Subject) exists or not in the knowledge graph.
        To be able to do this, the original Object (which becomes the Subject in this case) needs to be a DBpedia resource/
        entity. If it is a literal String, then the check is not performed (because Subject always needs to be a resource).
        :param triple: a triple of type triple.Triple
        :type triple: triple.Triple
        :param transitive: whether a check should also be done for entities that are in the sameAs relation with the subject
        :type transitive: bool
        :return: True if the opposite relation triple exists, False otherwise
        :rtype: bool
        """
        exists = [self.check_triple_existence(obj, triple.relation, triple.subject, transitive) for obj in triple.objects
                  if obj.startswith("http://dbpedia.org/resource")]
        if len(exists) == 0:
            return False
        # return any(exists) #all or any?
        return all(exists)

    def check_triple_existence(self, subject, relation, obj, transitive=False):
        """
        Checks if a triple exists or not in the knowledge graph
        :param subject: triple's subject (must be prepended by "http://dbpedia.org/resource/")
        :type subject: str
        :param relation: triple's relation/predicate/property (must be prepended by "http://dbpedia.org/ontology/")
        :type relation: str
        :param obj: triple's object
        :type obj: str
        :param transitive: whether a check should also be done for entities that are in the sameAs relation with the subject
        :type transitive: bool
        :return: True if triple exists, False otherwise
        :rtype: bool
        """
        # obj_query = obj.rsplit('/')[-1]
        if obj.startswith("http://dbpedia.org/resource"):
            obj_query = "<" + obj + ">"
        else:
            obj_query = '"{}"'.format(obj)
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                ASK {{
                  <{0}> dbo:{1} {2} .
                }}
                """.format(subject, relation.rsplit('/')[-1], obj_query)
        if transitive:
            query = "DEFINE input:same-as \"yes\"" + query
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Checking triple existence: %s, %s, %s", subject, relation, obj)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Check triple existence failed with status code " + results.responses.status)
        return results.convert()["boolean"]

    def get_triples(self, subject, relation, transitive=False):
        """
        Get triples from Knowledge Graph that have the given subject and relation.
        :param subject: triple's subject (must be prepended by "http://dbpedia.org/resource/")
        :type subject: str
        :param relation: triple's relation (must be prepended by "http://dbpedia.org/ontology/")
        :return: list of triples (triple.Triple) that exist in the knowledge graph, or None if such triple doesn't exist
        :param transitive: whether a check should also be done for entities that are in the sameAs relation with the subject
        :type transitive: bool
        :rtype: list or None
        """
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                SELECT ?o WHERE{{
                <{0}> dbo:{1} ?o .
                }}
                """.format(subject, relation.rsplit('/')[-1])
        if transitive:
            query = "DEFINE input:same-as \"yes\"" + query
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Getting triples given relation: %s, %s", subject, relation)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Get triples given relation failed with status code " + results.responses.status)
        results = results.convert()
        if len(results["results"]["bindings"]) > 0:
            return [Triple(subject, relation, [res["o"]["value"]]) for res in results["results"]["bindings"]]
        return None

    def get_relation_triples(self, subject, obj, transitive=False):
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                SELECT ?p WHERE{{
                <{0}> ?p <{1}> .
                }}
                """.format(subject, obj)
        if transitive:
            query = "DEFINE input:same-as \"yes\"" + query
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Getting triples: %s, %s", subject, obj)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Get triples failed with status code " + results.responses.status)
        results = results.convert()
        if len(results["results"]["bindings"]) > 0:
            return [Triple(subject, res["p"]["value"], [obj]) for res in results["results"]["bindings"]]
        return None

    def get_entity(self, subject, transitive=False):
        """
        Get all triples that the subject or entity has in the knowledge graphs.
        :param subject: triple's subject
        :type subject: str
        :param transitive: whether a check should also be done for entities that are in the sameAs relation with the subject
        :type transitive: bool
        :return: list of all triples that the subject has in the knowledge graph, or None if the subject doesn't exist
        :rtype: list or None
        """
        if not subject.startswith("http://dbpedia.org/resource"):
            subject = "http://dbpedia.org/resource/" + subject
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                SELECT ?r ?o WHERE{{
                <{0}> ?r ?o .
                }}
                """.format(subject)
        if transitive:
            query = "DEFINE input:same-as \"yes\"" + query
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Getting entity: %s,", subject)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Get entity failed with status code " + results.responses.status)
        results = results.convert()
        if len(results["results"]["bindings"]) > 0:
            return [Triple(subject, res["r"]["value"], [res["o"]["value"]]) for res in results["results"]["bindings"]]
        return None

    def insert_triple_object(self, triple):
        """
        Inserts triple to the knowledge graph.
        :param triple: a triple of type triple.Triple
        :type triple: triple.Triple
        """
        for obj in triple.objects:
            self.insert_triple(triple.subject, triple.relation, obj)

    def insert_triple(self, subject, relation, obj):
        """
        Inserts triple to the knowledge graph
        :param subject: triple's subject (must be prepended by "http://dbpedia.org/resource/")
        :type subject: str
        :param relation: triple's relation/predicate/property (must be prepended by "http://dbpedia.org/ontology/")
        :type relation: str
        :param obj: triple's object
        :type obj: str
        """
        # obj_query = obj.rsplit('/')[-1]
        if obj.startswith("http://dbpedia.org/resource"):
            obj_query = "<" + obj + ">"
        else:
            obj_query = '"{}"'.format(obj)
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                INSERT DATA
                {{
                    GRAPH <http://dbpedia.org>
                    {{
                        <{0}> dbo:{1} {2} .
                    }}
                }}
                """.format(subject, relation.rsplit('/')[-1], obj_query)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Inserting triple: %s, %s, %s", subject, relation, obj)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Insert triple failed with status code " + results.responses.status)

    def delete_triple_object(self, triple, transitive=False):
        """
        Deletes triple from the knowledge graph.
        :param triple: a triple of type triple.Triple
        :type triple: triple.Triple
        :param transitive: whether the delete should also be done for entities that are in the sameAs relation with the subject
        :type transitive: bool
        """
        for obj in triple.objects:
            self.delete_triple(triple.subject, triple.relation, obj)
        if transitive is True:
            same_entities = self.get_same_entities(triple.subject)
            for ent in same_entities:
                self.delete_triple(ent, triple.relation, obj)

    def delete_triple(self, subject, relation, obj):
        """
        Deletes triple from the knowledge graph.
        :param subject: triple's subject (must be prepended by "http://dbpedia.org/resource/")
        :type subject: str
        :param relation: triple's relation/predicate/property (must be prepended by "http://dbpedia.org/ontology/")
        :type relation: str
        :param obj: triple's object
        :type obj: str
        """
        # obj_query = obj.rsplit('/')[-1]
        if obj.startswith("http://dbpedia.org/resource"):
            obj_query = "<" + obj + ">"
        else:
            obj_query = '"{}"'.format(obj)
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                DELETE DATA
                {{
                  GRAPH <http://dbpedia.org>
                  {{
                    <{0}> dbo:{1} {2} .
                  }}
                }} 
                """.format(subject, relation.rsplit('/')[-1], obj_query)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Deleting triple: %s, %s, %s", subject, relation, obj)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Delete triple failed with status code " + results.responses.status)

    def get_same_entities(self, entity):
        """
        Return DBpedia entities that have the owl:sameAs relation with the input.
        They should be considered as the same entity.
        :param entity: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity: str
        :return: a list of DBpedia entities that have the owl:sameAs relation with the input
        :rtype: list
        """
        query = """
                PREFIX owl:<http://www.w3.org/2002/07/owl#>
                SELECT ?o WHERE{{
                <{0}> owl:sameAs ?o .
                }}
                """.format(entity)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Getting same entities for: %s", entity)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Get same entities failed with status code " + results.responses.status)
        results = results.convert()
        if len(results["results"]["bindings"]) > 0:
            return [res["o"]["value"] for res in results["results"]["bindings"]]
        return []

    def add_sameAs_relation(self, entity_a, entity_b):
        """
        Add a sameAs relation between two entities.
        :param entity_a: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity_a: str
        :param entity_b: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity_b: str
        """
        query = """
                PREFIX owl:<http://www.w3.org/2002/07/owl#>
                INSERT DATA {{
                  GRAPH <http://dbpedia.org>
                  {{
                    <{0}> owl:sameAs <{1}> .
                    <{1}> owl:sameAs <{0}> .
                  }}
                }}
                """.format(entity_a, entity_b)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Inserting sameAs relation between: %s, %s", entity_a, entity_b)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Insert sameAs relation failed with status code " + results.responses.status)

    def remove_sameAs_relation(self, entity_a, entity_b):
        """
        Remove the sameAs relation between two entities.
        :param entity_a: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity_a: str
        :param entity_b: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity_b: str
        """
        query = """
                PREFIX owl:<http://www.w3.org/2002/07/owl#>
                DELETE DATA {{
                  GRAPH <http://dbpedia.org>
                  {{
                    <{0}> owl:sameAs <{1}> .
                    <{1}> owl:sameAs <{0}> .
                  }}
                }}
                """.format(entity_a, entity_b)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Removing sameAs relation between: %s, %s", entity_a, entity_b)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Removing sameAs relation failed with status code " + results.responses.status)

    def check_sameAs_relation(self, entity_a, entity_b):
        """
        Check the sameAs relation existence between two entities.
        :param entity_a: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity_a: str
        :param entity_b: a DBpedia resource/entity (must be prepended by "http://dbpedia.org/resource/")
        :type entity_b: str
        """
        query = """
                PREFIX owl:<http://www.w3.org/2002/07/owl#>
                ASK {{
                  <{0}> owl:sameAs <{1}> .
                  <{1}> owl:sameAs <{0}> .
                }}
                """.format(entity_a, entity_b)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        self.logger.info("Checking sameAs relation existence between: %s, %s", entity_a, entity_b)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Check sameAs relation existence failed with status code " + results.responses.status)
        return results.convert()["boolean"]

if __name__ == '__main__':
    wrapper = KnowledgeGraphWrapper()
    # triples = wrapper.get_triples("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/education")
    # pprint.pprint(triples)

    # triples = wrapper.get_entity("http://dbpedia.org/resource/Albertus_Andito")
    # pprint.pprint(triples)
    #
    # wrapper.insert_triple("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/education",
    #                             "http://dbpedia.org/resource/SD_Aloysius")

    # print(wrapper.insert_triple("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/say",
    #                             "hello"))

    # wrapper.delete_triple("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/education",
    #                             "http://dbpedia.org/resource/SD_Aloysius")

    # res = wrapper.check_triple_existence("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/education",
    #                                "http://dbpedia.org/resource/University_of_Sussex")
    # print(res)

    # wrapper.insert_triple("http://dbpedia.org/resource/Mr_Giuliani", "http://dbpedia.org/ontology/ignore", "http://dbpedia.org/resource/Social_norms")

    triples = wrapper.get_entity("http://dbpedia.org/resource/Mr_Giuliani")
    print(triples)

    triples = wrapper.get_entity("Mr_Giuliani")
    print(triples)

    # wrapper.delete_triple("http://dbpedia.org/resource/Mr_Giuliani", "http://dbpedia.org/ontology/repeat", "unsubstantiated claims")
    # wrapper.delete_triple("http://dbpedia.org/resource/Mr_Giuliani", "http://dbpedia.org/ontology/claim",
    #                       "http://dbpedia.org/resource/Electoral_fraud")

    resource = "http://dbpedia.org/resource/Mr_Giulani"
    print(wrapper.check_resource_existence(resource))

    wrapper.add_sameAs_relation("http://dbpedia.org/resource/Mr_Giuliani", "http://dbpedia.org/resource/Rudy_Giuliani")
    print(wrapper.get_entity("http://dbpedia.org/resource/Mr_Giuliani"))

    res = wrapper.check_triple_existence("http://dbpedia.org/resource/Rudy_Giuliani", "http://dbpedia.org/ontology/admit",
                                   "Sunday", transitive=True)
    print(res)

    res = wrapper.check_sameAs_relation("http://dbpedia.org/resource/Rudy_Giuliani", "http://dbpedia.org/resource/Mr_Giuliani")
    print(res)

    # wrapper.remove_sameAs_relation("http://dbpedia.org/resource/Mr_Giuliani", "http://dbpedia.org/resource/Rudy_Giuliani")
    # print(wrapper.get_entity("http://dbpedia.org/resource/Mr_Giuliani"))

    res = wrapper.get_same_entities("http://dbpedia.org/resource/Rudy_Giuliani")
    print(res)

    res = wrapper.get_relation_triples("http://dbpedia.org/resource/Rudy_Giuliani", "http://dbpedia.org/resource/Social_distancing",
                                       transitive=True)
    print(res)