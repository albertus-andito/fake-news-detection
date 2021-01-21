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

    def get_triples(self, subject, relation):
        """
        Get triples from Knowledge Graph that have the given subject and relation.
        :param subject: triple's subject (must be prepended by "http://dbpedia.org/resource/")
        :type subject: str
        :param relation: triple's relation (must be prepended by "http://dbpedia.org/ontology/")
        :return: list of triples (triple.Triple) that exist in the knowledge graph, or None if such triple doesn't exist
        :rtype: list or None
        """
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                SELECT ?o WHERE{{
                :{0} dbo:{1} ?o .
                }}
                """.format(subject.rsplit('/')[-1], relation.rsplit('/')[-1])
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Get entity failed with status code " + results.responses.status)
        results = results.convert()
        if len(results["results"]["bindings"]) > 0:
            return [Triple(subject, relation, res["o"]["value"]) for res in results["results"]["bindings"]]
        return None

    def get_entity(self, subject):
        """
        Get all triples that the subject or entity has in the knowledge graphs.
        :param subject: triple's subject
        :type subject: str
        :return: list of all triples that the subject has in the knowledge graph, or None if the subject doesn't exist
        :rtype: list or None
        """
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                SELECT ?r ?o WHERE{{
                :{0} ?r ?o .
                }}
                """.format(subject.rsplit('/')[-1])
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Get entity failed with status code " + results.responses.status)
        results = results.convert()
        if len(results["results"]["bindings"]) > 0:
            return [Triple(subject, res["r"]["value"], res["o"]["value"]) for res in results["results"]["bindings"]]
        return None

    def insert_triple(self, triple):
        """
        Inserts triple to the knowledge graph.
        :param triple: a triple of type triple.Triple
        :type triple: triple.Triple
        """
        for obj in triple.objs:
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
        obj_query = obj.rsplit('/')[-1]
        if obj.startswith("http://dbpedia.org/resource"):
            obj_query = ":" + obj_query
        else:
            obj_query = '"{}"'.format(obj_query)
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                INSERT DATA
                {{
                    GRAPH <http://dbpedia.org>
                    {{
                        :{0} dbo:{1} {2} .
                    }}
                }}
                """.format(subject.rsplit('/')[-1], relation.rsplit('/')[-1], obj_query)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Get entity failed with status code " + results.responses.status)

    def delete_triple(self, triple):
        """
        Deletes triple from the knowledge graph.
        :param triple: a triple of type triple.Triple
        :type triple: triple.Triple
        """
        for obj in triple.objs:
            self.delete_triple(triple.subject, triple.relation, obj)

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
        obj_query = obj.rsplit('/')[-1]
        if obj.startswith("http://dbpedia.org/resource"):
            obj_query = ":" + obj_query
        else:
            obj_query = '"{}"'.format(obj_query)
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                DELETE DATA
                {{
                  GRAPH <http://dbpedia.org>
                  {{
                    :{0} dbo:{1} {2} .
                  }}
                }} 
                """.format(subject.rsplit('/')[-1], relation.rsplit('/')[-1], obj_query)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query()
        if results.response.status != 200:
            raise Exception("Delete triple failed with status code " + results.responses.status)


if __name__ == '__main__':
    wrapper = KnowledgeGraphWrapper()
    # triples = wrapper.get_triples("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/education")
    # pprint.pprint(triples)

    triples = wrapper.get_entity("http://dbpedia.org/resource/Albertus_Andito")
    pprint.pprint(triples)

    wrapper.insert_triple("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/education",
                                "http://dbpedia.org/resource/SD_Aloysius")

    # print(wrapper.insert_triple("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/say",
    #                             "hello"))

    wrapper.delete_triple("http://dbpedia.org/resource/Albertus_Andito", "http://dbpedia.org/ontology/education",
                                "http://dbpedia.org/resource/SD_Aloysius")
