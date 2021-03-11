from flask import Blueprint, request
from urllib.parse import urlparse

from articlescraper.scrapers import IndependentScraper, BbcScraper, GuardianScraper, GenericScraper
from nonexactmatchfactchecker import NonExactMatchFactChecker
from exactmatchfactchecker import ExactMatchFactChecker
from triple import Triple

fc_api = Blueprint('fc_api', __name__)

exact_match_fc = ExactMatchFactChecker()
non_exact_match_fc = NonExactMatchFactChecker()
bbc_scraper = BbcScraper()
guardian_scraper = GuardianScraper()
independent_scraper = IndependentScraper()
generic_scraper = GenericScraper()


def scrape_text_from_url(url):
    """
    Scrapes text from the url given. It uses the generic scraper if the url is not for BBC, Guardian, or Independent.
    :param url: url
    :type url: str
    :return: text scraped from the url
    :rtype: str
    """
    if urlparse(url).netloc == 'www.bbc.co.uk':
        scraped = bbc_scraper.scrape(url)
    elif urlparse(url).netloc == 'www.theguardian.com':
        scraped = guardian_scraper.scrape(url)
    elif urlparse(url).netloc == 'www.independent.co.uk':
        scraped = independent_scraper.scrape(url)
    else:
        scraped = generic_scraper.scrape(url)
    return scraped['texts']


@fc_api.route('/')
def hello_world():
    return 'Hello Fact Checker'


@fc_api.route('/exact/fact-check/url/', methods=['POST'])
def exact_match_fact_check_url():
    """
    Exact match fact checking method, where the input is a url.
    ---
    tags:
      - Fact-Checker
    consumes:
      - application/json
    parameters:
      - in: body
        name: url
        schema:
          id: url
          type: object
          properties:
            url:
              type: string
            extraction_scope:
              type: string
              enum: [noun_phrases, named_entities, all]
        required: true
    responses:
      200:
        description: Fact-checking result
        schema:
          id: fact_checking_sentences_result
    """
    url = request.get_json()['url']
    extraction_scope = request.get_json()['extraction_scope']
    text = scrape_text_from_url(url)
    results = exact_match_fc.fact_check(text, extraction_scope)
    triples = [{'sentence': sentence, 'triples': [{'triple': triple.to_dict(), 'result': result,
                                                   'other_triples': [other.to_dict() for other in other_triples]}
                                                  for (triple, (result, other_triples)) in triples.items()]}
               for sentence, triples in results]
    return {'triples': triples}, 200



@fc_api.route('/exact/fact-check/triples/transitive/', methods=['POST'])
def transitive_exact_match_fact_check_triples():
    """
    Exact-match closed-world fact checking method, where the input is a list of triples.
    It also checks for entities with the sameAs relation.
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
    responses:
      200:
        description: Fact-checking result
        schema:
          id: fact_checking_result
    """
    input_triples = request.get_json()
    input_triples = [Triple.from_dict(triple) for triple in input_triples]
    triples = exact_match_fc.fact_check_triples(input_triples, transitive=True)
    triples = [
        {'triple': triple.to_dict(), 'result': result, 'other_triples': [other.to_dict() for other in other_triples]}
        for (triple, (result, other_triples)) in triples.items()]
    return {'triples': triples}, 200


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
                    $ref: '#/definitions/triples_array'
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
            extraction_scope:
              type: string
              enum: [noun_phrases, named_entities, all]
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
                          $ref: '#/definitions/triples_array'
            truthfulness:
              type: number
    """
    text = request.get_json()['text']
    extraction_scope = request.get_json()['extraction_scope']
    results = exact_match_fc.fact_check(text, extraction_scope)
    triples = [{'sentence': sentence, 'triples': [{'triple': triple.to_dict(), 'result': result,
                                                   'other_triples': [other.to_dict() for other in other_triples]}
                                                  for (triple, (result, other_triples)) in triples.items()]}
               for sentence, triples in results]
    return {'triples': triples}, 200


@fc_api.route('/non-exact/fact-check/url/', methods=['POST'])
def non_exact_match_fact_check_url():
    """
    Non-Exact match fact checking method, where the input is a url.
    ---
    tags:
      - Fact-Checker
    consumes:
      - application/json
    parameters:
      - in: body
        name: url
        schema:
          id: url
    responses:
      200:
        description: Fact-checking result
        schema:
          id: fact_checking_sentences_result
    """
    url = request.get_json()['url']
    text = scrape_text_from_url(url)
    extraction_scope = request.get_json()['extraction_scope']
    results = non_exact_match_fc.fact_check(text, extraction_scope)
    triples = [{'sentence': sentence, 'triples': [{'triple': triple.to_dict(), 'result': result,
                                                   'other_triples': [other.to_dict() for other in other_triples]}
                                                  for (triple, (result, other_triples)) in triples.items()]}
               for sentence, triples in results]
    return {'triples': triples}, 200


@fc_api.route('/non-exact/fact-check/triples-sentences/', methods=['POST'])
def non_exact_match_fact_check_triples_sentences():
    """
    Non-exact match closed-world fact checking method, where the input is a list of triples.
    The sentence is included with the triples, only for matching purposes.
    ---
    tags:
      - Fact-Checker
    consumes:
      - application/json
    parameters:
      - in: body
        name: triples_sentences_array
        schema:
          id: triples_sentences_array
          type: array
          items:
            type: object
            properties:
              sentence:
                type: string
              triples:
                $ref: '#/definitions/triples_array'
        required: true
    responses:
      200:
        description: Fact-checking result
        schema:
          id: fact_checking_sentences_result
    """
    input = request.get_json()
    all_triples = []
    for sentence in input:
        input_triples = [Triple.from_dict(triple) for triple in sentence['triples']]
        triples = non_exact_match_fc.fact_check_triples(input_triples)
        triples = [
            {'triple': triple.to_dict(), 'result': result, 'other_triples': [other.to_dict() for other in other_triples]}
            for (triple, (result, other_triples)) in triples.items()]
        all_triples.append({
            'sentence': sentence['sentence'],
            'triples': triples
        })
    return {'triples': all_triples}, 200


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
    triples = non_exact_match_fc.fact_check_triples(input_triples)
    triples = [
        {'triple': triple.to_dict(), 'result': result, 'other_triples': [other.to_dict() for other in other_triples]}
        for (triple, (result, other_triples)) in triples.items()]
    return {'triples': triples}, 200


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
    extraction_scope = request.get_json()['extraction_scope']
    results = non_exact_match_fc.fact_check(text, extraction_scope)
    triples = [{'sentence': sentence, 'triples': [{'triple': triple.to_dict(), 'result': result,
                                                   'other_triples': [other.to_dict() for other in other_triples]}
                                                  for (triple, (result, other_triples)) in triples.items()]}
               for sentence, triples in results]
    return {'triples': triples}, 200
