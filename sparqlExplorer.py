from SPARQLWrapper import SPARQLWrapper, JSON, XML, RDFXML

sparql = SPARQLWrapper("http://localhost:8890/sparql")

# sparql.setQuery("""
#     PREFIX : <http://dbpedia.org/resource/>
#     PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
#     SELECT ?b ?c WHERE{
#     :Albertus_Andito ?b ?c .
#     }
# """)


# sparql.setQuery("""
#     PREFIX : <http://dbpedia.org/resource/>
#     INSERT DATA
#     {
#       GRAPH <testgraph>
#       {
#         :Albertus_Andito dbo:education :University_of_Sussex .
#       }
#     }
# """)

sparql.setQuery("""
    PREFIX : <http://dbpedia.org/resource/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT ?name WHERE{
    ?name dbo:education :University_of_Sussex .
    }
""")

sparql.setReturnFormat(JSON)

results = sparql.query().convert()

for result in results["results"]["bindings"]:
    print(result["name"]["value"])

