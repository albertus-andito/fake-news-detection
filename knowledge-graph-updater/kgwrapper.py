import os
from dotenv import load_dotenv
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON, XML, RDFXML

class KnowledgeGraphWrapper:

    def __init__(self):
        load_dotenv(dotenv_path=Path('../.env'))
        self.sparql = SPARQLWrapper(os.getenv("SPARQL_ENDPOINT"))

    def select_triple(self, subject, relation):
        query = """
                PREFIX : <http://dbpedia.org/resource/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT ?o WHERE{{
                :{0} dbo:{1} ?o .
                }}
                """.format(subject, relation)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()
        print(results["results"]["bindings"][0]["o"]["value"])

if __name__ == '__main__':
    wrapper = KnowledgeGraphWrapper()
    wrapper.select_triple("Albertus_Andito", "education")