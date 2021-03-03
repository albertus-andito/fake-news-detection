from flask import Blueprint, request

from nonexactmatchfactchecker import NonExactMatchFactChecker
from exactmatchfactchecker import ExactMatchFactChecker
from triple import Triple

fc_api = Blueprint('fc_api', __name__)

exact_match_fc = ExactMatchFactChecker()
non_exact_match_fc = NonExactMatchFactChecker()

@fc_api.route('/')
def hello_world():
    return 'Hello Fact Checker'


@fc_api.route('/exact/fact-check/triples/', methods=['POST'])
def exact_match_fact_check_triples():
    """
    Exact-match closed-world fact checking method, where the input is a list of triples.
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
                  result:
                    type: string
                    enum: [exists, conflicts, possible, none]
                  other_triples:
                    type: array
                    description: list of triples that support the result (conflicting triples, possible triples)
                    $ref: '#/definitions/triples'
            truthfulness:
              type: number
    """
    input_triples = request.get_json()
    input_triples = [Triple.from_dict(triple) for triple in input_triples]
    triples = exact_match_fc.fact_check_triples(input_triples)
    triples = [{'triple': triple.to_dict(), 'result': result, 'other_triples': [other.to_dict() for other in other_triples]}
               for (triple, (result, other_triples)) in triples.items()]
    return {'triples': triples}, 200


@fc_api.route('/exact/fact-check/', methods=['POST'])
def exact_match_fact_check():
    """
    Exact-match closed-world fact checking method, where the input is a text.
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
                        result:
                          type: string
                          enum: [exists, conflicts, possible, none]
                        other_triples:
                          type: array
                          description: list of triples that support the result (conflicting triples, possible triples)
                          $ref: '#/definitions/triples'
            truthfulness:
              type: number
    """
    text = request.get_json()['text']
    results = exact_match_fc.fact_check(text)
    triples = [{'sentence': sentence, 'triples': [{'triple': triple.to_dict(), 'result': result,
                                                   'other_triples': [other.to_dict() for other in other_triples]}
                                                  for (triple, (result, other_triples)) in triples.items()]}
               for sentence, triples in results]
    return {'triples': triples}, 200


@fc_api.route('/non-exact/fact-check/triples/', methods=['POST'])
def non_exact_match_fact_check_triples():
    """
    Non-exact match closed-world fact checking method, where the input is a list of triples.
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
    triples, truthfulness = non_exact_match_fc.fact_check_triples(input_triples)
    triples = [{'triple': triple.to_dict(), 'exists': exists} for triple_set in triples
               for (triple, exists) in triple_set.items()]
    return {'triples': triples, 'truthfulness': truthfulness}, 200


@fc_api.route('/non-exact/fact-check/', methods=['POST'])
def non_exact_match_fact_check():
    """
    Non-exact match fact checking method, where the input is a text.
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
    results, truthfulness = non_exact_match_fc.fact_check(text)
    triples = [{'sentence': sentence, 'triples': [{'triple': triple.to_dict(), 'exists': exists}
                                                  for (triple, exists) in triples.items()]}
               for sentence, triples in results]
    return {'triples': triples, 'truthfulness': truthfulness}, 200
