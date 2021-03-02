from flask import Blueprint, request

from nonexactmatchfactchecker import NonExactMatchFactChecker
from exactmatchfactchecker import ExactMatchFactChecker
from triple import Triple

fc_api = Blueprint('fc_api', __name__)

simple_fact_checker = ExactMatchFactChecker()
better_fact_checker = NonExactMatchFactChecker()

@fc_api.route('/')
def hello_world():
    return 'Hello Fact Checker'


@fc_api.route('/simple/fact-check/triples/', methods=['POST'])
def simple_fact_check_triples():
    """
    Simple closed-world fact checking method, where the input is a list of triples.
    ---
    tags:
      - Fact-Checker
    consumes:
      - application/json
    parameters:
      - in: body
        name: triples_array
        schema:
          id: triples_array
          type: array
          items:
            type: object
            properties:
              subject:
                type: string
              relation:
                type: string
              objects:
                type: array
                items:
                  type: string
        required: true
    responses:
      200:
        description: Fact-checking result
        schema:
          id: fact_checking_result
          properties:
            triples:
              type: array
              items:
                type: object
                properties:
                  triple:
                    type: object
                    properties:
                      subject:
                        type: string
                      relation:
                        type: string
                      objects:
                        type: array
                        items:
                          type: string
                  exists:
                    type: boolean
            truthfulness:
              type: number
    """
    input_triples = request.get_json()
    input_triples = [Triple.from_dict(triple) for triple in input_triples]
    triples, truthfulness = simple_fact_checker.fact_check_triples(input_triples)
    triples = [{'triple': triple.to_dict(), 'exists': exists} for (triple, exists) in triples.items()]
    return {'triples': triples, 'truthfulness': truthfulness}, 200


@fc_api.route('/simple/fact-check/', methods=['POST'])
def simple_fact_check():
    """
    Simple closed-world fact checking method, where the input is a text.
    ---
    tags:
      - Fact-Checker
    consumes:
      - application/json
    parameters:
      - in: body
        name: text
        schema:
          id: text
          type: object
          properties:
            text:
              type: string
        required: true
    responses:
      200:
        description: Fact-checking result
        schema:
          id: fact_checking_sentences_result
          properties:
            triples:
              type: array
              items:
                type: object
                properties:
                  sentence:
                    type: string
                  triples:
                    type: array
                    items:
                      type: object
                      properties:
                        triple:
                          type: object
                          properties:
                            subject:
                              type: string
                            relation:
                              type: string
                            objects:
                              type: array
                              items:
                                type: string
                        exists:
                          type: boolean
            truthfulness:
              type: number
    """
    text = request.get_json()['text']
    results, truthfulness = simple_fact_checker.fact_check(text)
    triples = [{'sentence': sentence, 'triples': [{'triple': triple.to_dict(), 'exists': exists}
                                                  for (triple, exists) in triples.items()]}
               for sentence, triples in results]
    return {'triples': triples, 'truthfulness': truthfulness}, 200


@fc_api.route('/better/fact-check/triples/', methods=['POST'])
def better_fact_check_triples():
    """
        Simple closed-world fact checking method, where the input is a list of triples.
        ---
        tags:
          - Fact-Checker
        consumes:
          - application/json
        parameters:
          - in: body
            name: triples_array
            schema:
              id: triples_array
            required: true
        responses:
          200:
            description: Fact-checking result
            schema:
              id: fact_checking_result
    """
    input_triples = request.get_json()
    input_triples = [Triple.from_dict(triple) for triple in input_triples]
    triples, truthfulness = better_fact_checker.fact_check_triples(input_triples)
    triples = [{'triple': triple.to_dict(), 'exists': exists} for triple_set in triples
               for (triple, exists) in triple_set.items()]
    return {'triples': triples, 'truthfulness': truthfulness}, 200


@fc_api.route('/better/fact-check/', methods=['POST'])
def better_fact_check():
    """
    Better fact checking method, where the input is a text.
    ---
    tags:
      - Fact-Checker
    consumes:
      - application/json
    parameters:
      - in: body
        name: text
        schema:
          id: text
        required: true
    responses:
      200:
        description: Fact-checking result
        schema:
          id: fact_checking_sentences_result
    """
    text = request.get_json()['text']
    results, truthfulness = better_fact_checker.fact_check(text)
    triples = [{'sentence': sentence, 'triples': [{'triple': triple.to_dict(), 'exists': exists}
                                                  for (triple, exists) in triples.items()]}
               for sentence, triples in results]
    return {'triples': triples, 'truthfulness': truthfulness}, 200
