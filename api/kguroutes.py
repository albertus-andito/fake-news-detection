import logging
import os
import threading
from flask import Blueprint, request

from definitions import ROOT_DIR, LOGGER_CONFIG_PATH
from kgupdater import KnowledgeGraphUpdater

kgu = KnowledgeGraphUpdater()
kgu_api = Blueprint('kgu_api', __name__)

LOGFILE_PATH = os.path.join(ROOT_DIR, 'logs', 'kgu-routes.log').replace("\\", "/")
logging.config.fileConfig(LOGGER_CONFIG_PATH,
                          defaults={'logfilename': LOGFILE_PATH},
                          disable_existing_loggers=False)
logger = logging.getLogger()

updating = False  # flag for update_missed_knowledge operation


@kgu_api.route('/updates/status/')
def updates_status():
    """
    Checks the status of the update_missed_knowledge operation.
    There can only be one update_missed_knowledge operation running at a time.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    responses:
      202:
        description: The update operation is still processing.
        schema:
          id: standard_message
          properties:
            message:
              type: string
      200:
        description: The update operation is done. Another request to update can be made.
        schema:
          id: standard_message
    """
    if updating is True:
        return {'message': 'Still processing...'}, 202
    return {'message': 'Done. Another request to update can be made.'}, 200


@kgu_api.route('/updates')
def trigger_updates():
    """
    Triggers an update that will extract triples from stored articles, and add non-conflicting triples to knowledge graph, if specified.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    parameters:
      - name: auto_update
        in: query
        description: whether the non-conflicting extracted triples are added to the knowledge graph automatically or not.
        required: false
        type: Boolean
      - name: extraction_scope
        in: query
        description: The scope of the extraction, deciding whether it should include only relations between
                     'named_entities', 'noun_phrases', or 'all.
        required: false
        type: String
    responses:
      202:
        description: Request to update is submitted and being processed.
        schema:
          id: standard_message
      409:
        description: An update is already in progress. Check /kgu/updates/status for the status of the update.
        schema:
          id: standard_message
    """
    if updating is False:
        if request.args.get('auto_update') == 'true':
            auto_update = True
        elif request.args.get('auto_update') == 'false':
            auto_update = False
        else:
            auto_update = None
        if request.args.get('extraction_scope') is None:
            extraction_scope = None
        else:
            extraction_scope = request.args.get('extraction_scope')
        async_task = AsyncUpdate(kgu, kg_auto_update=auto_update, extraction_scope=extraction_scope)
        async_task.start()
        return {'message': 'Request submitted. Update is processing...'}, 202
    return {'message': 'An update is already in progress. Check /kgu/updates/status for the status'}, 409


@kgu_api.route('/article-triples/corefering-entities/')
def unresolved_corefering_entities():
    """
    Returns all unresolved corefering entities from all scraped articles.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    responses:
      200:
        description: Corefering entities of all articles returned successfully
        schema:
          id: all_coref_entities
          type: object
          properties:
            all_coref_entities:
              type: array
              items:
                type: object
                properties:
                  source:
                    type: str
                  coref_entities:
                    type: array
                    items:
                      type: object
                      properties:
                        main:
                          type: str
                        mentions:
                          type: array
                          items:
                            type: object
                            properties:
                              mention:
                                type: str
                              resolved:
                                type: boolean

    """
    return {'all_coref_entities': kgu.get_all_unresolved_corefering_entities()}, 200


@kgu_api.route('/article-triples/insert/', methods=['POST'])
def insert_article_triples():
    """
    Insert triples that were extracted from articles to the knowledge graph.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    consumes:
      - application/json
    parameters:
      - in: body
        name: article_triples
        schema:
          id: article_triples_array
          type: array
          items:
            $ref: '#/definitions/article_triples'
        required: true
    responses:
      200:
        description: Triples were inserted successfully.
        schema:
          id: standard_message
    """
    data = request.get_json()
    kgu.insert_articles_knowledge(data)
    return {"message": "Triples inserted."}, 200


@kgu_api.route('/article-triples/delete/<path:source>', methods=['DELETE'])
def delete_all_article_triples(source):
    """
    Removes all triples of the specified article from the knowledge graph.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    parameters:
      - name: source
        in: path
        description: URL of article whose triples are going to be removed from the knowledge graph.
        type: string
        required: true
    responses:
      200:
        description: All triples from the article have been successfully deleted.
        schema:
          id: article_url_with_message
          properties:
            source:
              type: string
            message:
              type: string
    """
    kgu.delete_all_knowledge_from_article(source)
    return {'source': source, 'message': 'All triples deleted.'}, 200


@kgu_api.route('/article-triples/conflicts/<path:source>')
def conflicts_from_article(source):
    """
    Returns triples from the specified article that have conflicts with the knowledge graph.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    definitions:
      conflicted_triples:
        type: object
        properties:
          source:
            type: string
          conflicts:
            type: array
            description: array of conflicted triples extracted from the article
            items:
              type: object
              properties:
                toBeInserted:
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
                inKnowledgeGraph:
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
                added:
                  type: boolean
                  description: whether the conflicted triple was added to the knowledge graph at some point
    parameters:
      - name: source
        in: path
        description: URL of article whose conflicted triples are going to be retrieved.
        type: string
        required: true
    responses:
      200:
        description: Conflicted triples of the article returned successfully
        schema:
          $ref: '#/definitions/conflicted_triples'
      404:
        description: No conflicted triples for the specified article are not found.
        schema:
          id: article_url_with_message
    """
    conflicts = kgu.get_article_conflicts(source)
    if conflicts is None:
        return {'source': source, 'message': 'No conflicts found for this article'}, 404
    return {'source': source, 'conflicts': conflicts}, 200


@kgu_api.route('/article-triples/conflicts/')
def conflicts_from_articles():
    """
    Returns all conflicted triples from all scraped articles.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    responses:
      200:
        description: Conflicted triples of all articles returned successfully
        schema:
          id: all_conflicted_triples
          type: object
          properties:
            all_conflicts:
              type: array
              items:
                $ref: '#/definitions/conflicted_triples'
    """
    return {'all_conflicts': kgu.get_all_article_conflicts()}, 200


@kgu_api.route('/article-triples/pending/<path:source>')
def pending_triples_from_article(source):
    """
    Returns pending triples (that are currently not in the knowledge graph) for the specified article.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    parameters:
      - name: source
        in: path
        description: URL of article whose pending triples are going to be retrieved.
        type: string
        required: true
    responses:
      200:
        description: Pending triples of the article returned successfully
        schema:
          $ref: '#/definitions/article_triples'
      404:
        description: No pending triples for the specified article are not found.
        schema:
          id: article_url_with_message
    """
    pending = kgu.get_article_pending_knowledge(source)
    if pending is None:
        return {'source': source, 'message': 'No pending triples (to be added to the knowledge graph) found for '
                                             'this article'}, 404
    return {'source': source, 'triples': pending}


@kgu_api.route('/article-triples/pending/', methods=['DELETE'])
def delete_pending_triples_from_articles():
    """
    Delete pending article triples that have not been added to the knowledge graph.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    consumes:
      - application/json
    parameters:
      - in: body
        name: article_triples
        schema:
          id: article_triples_array
          type: array
          items:
            $ref: '#/definitions/article_triples'
        required: true
    responses:
      200:
        description: Pending triples were deleted successfully.
        schema:
          id: standard_message
    """
    data = request.get_json()
    for article_triple in data:
        kgu.delete_article_pending_knowledge(article_triple['source'], article_triple['triples'])
    return {'message': 'Pending triples deleted.'}, 200


@kgu_api.route('/article-triples/pending/')
def pending_triples_from_articles():
    """
    Returns all pending triples from all scraped articles.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    responses:
      200:
        description: Pending triples of all articles returned successfully
        schema:
          id: all_pending_triples
          type: object
          properties:
            all_pending:
              type: array
              items:
                $ref: '#/definitions/article_triples'
    """
    return {'all_pending': kgu.get_all_pending_knowledge()}, 200


@kgu_api.route('/article-triples/<path:source>')
def triples_from_article(source):
    """
    Returns all triples from the specified article.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    definitions:
      article_triples:
        properties:
          source:
            type: string
          triples:
            type: array
            description: array of sentences and triples extracted from the article
            items:
              type: object
              properties:
                sentence:
                  type: string
                triples:
                  type: array
                  description: array of triples
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
                      added:
                        type: boolean
                        description: whether the triple is currently added to the knowledge graph or not
    parameters:
      - name: source
        in: path
        description: URL of article whose triples are going to be retrieved from the knowledge graph.
        type: string
        required: true
    responses:
      200:
        description: Triples of the article returned successfully
        schema:
          $ref: '#/definitions/article_triples'
      404:
        description: Triples for the specified article are not found.
        schema:
          id: article_url_with_message
    """
    triples = kgu.get_article_knowledge(source)
    if triples is None:
        return {'source': source, 'message': 'Triples haven\'t been extracted from this article. Please '
                                             'call the /kgu/updates/ endpoint.'}, 404
    return {'source': source, 'triples': triples}, 200


@kgu_api.route('/article-triples/')
def triples_from_articles():
    """
    Returns all triples from all extracted articles.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    responses:
      200:
        description: Triples of all articles returned successfully
        schema:
          id: all_triples
          properties:
            all_triples:
              type: array
              items:
                $ref: '#/definitions/article_triples'
        """
    # TODO: add pagination
    return {'all_triples': kgu.get_all_articles_knowledge()}, 200


@kgu_api.route('/articles/extracted/')
def all_extracted_article_urls():
    """
    Returns all articles' URLs, headlines, and dates whose triples have been extracted.
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    responses:
      200:
        description: Array of articles URLs, headlines, and dates
        schema:
          id: articles
          properties:
            articles:
              type: array
              items:
                type: object
                properties:
                  source:
                    type: string
                  headlines:
                    type: string
                  date:
                    type: string
                    description: POSIX timestamp
    """
    return {'articles': kgu.get_all_extracted_articles()}, 200


@kgu_api.route('/articles/')
def all_article_urls():
    """
    Returns all articles' URLs, headlines, and dates
    ---
    tags:
      - Knowledge Graph Updater (Articles)
    responses:
      200:
        description: Array of articles URLs, headlines, and dates
        schema:
          id: articles
          properties:
            articles:
              type: array
              items:
                type: object
                properties:
                  source:
                    type: string
                  headlines:
                    type: string
                  date:
                    type: string
                    description: POSIX timestamp
    """
    return {'articles': kgu.get_all_articles()}, 200


@kgu_api.route('/triples/force/', methods=['POST'])
def force_insert_triples():
    """
    Insert triples to the knowledge graph, even if there are conflicts.
    ---
    tags:
      - Knowledge Graph Updater
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
        description: Triples were inserted successfully.
        schema:
          id: standard_message
    """
    data = request.get_json()
    if type(data) is list:
        for triple in data:
            kgu.insert_knowledge(triple, check_conflict=False)
    else:
        kgu.insert_knowledge(data, check_conflict=False)
    return {'message': 'All triples inserted.'}, 200


@kgu_api.route('/triples/')
def get_triples():
    """
    Returns triples that satisfy the specified conditions (subject, relation, or objects)
    ---
    tags:
      - Knowledge Graph Updater
    parameters:
      - name: subject
        in: query
        type: string
        required: true
      - name: relation
        in: query
        type: string
        required: true#
      - name: objects
        in: query
        type: array
        collectionFormat: multi
        items:
          type: string
        required: false
    responses:
      200:
        description: Triples in the knowledge graph that are related to the given subject and relation (and objects, if given)
        schema:
          id: triples
          properties:
            triples:
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
      404:
        description: No triples found in the knowledge graph with the given properties.
        schema:
          id: standard_message
    """
    subject = request.args.get('subject')
    relation = request.args.get('relation')
    objects = request.args.getlist('objects')
    triples = kgu.get_knowledge(subject, relation, objects)
    if triples is None or len(triples) == 0:
        return {'message': 'No triple found for the given properties in the knowledge graph.'}, 404
    return {'triples': triples}, 200


@kgu_api.route('/triples/', methods=['POST'])
def insert_triples():
    """
    Insert triples to knowledge graph. If a triple has conflicts, it will return the conflicts and not insert the triple.
    ---
    tags:
      - Knowledge Graph Updater
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
        description: Triples were inserted successfully.
        schema:
          id: standard_message
      409:
        description: There are some conflicting triples.
        schema:
          id: conflicts_with_message
          type: object
          properties:
            message:
              type: string
            conflicts:
              type: array
              description: array of conflicted triples in the knowledge graph
              items:
                type: object
                properties:
                  toBeInserted:
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
                  inKnowledgeGraph:
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
    """
    data = request.get_json()
    # Pair up the conflicts
    conflicts_list = [kgu.insert_knowledge(triple, check_conflict=True) for triple in data]
    conflicts_pairs = [(conflicts, to_be_inserted) for (conflicts, to_be_inserted) in zip(conflicts_list, data) if
                       conflicts is not None]
    conflicts_pairs = [(conflict, to_be_inserted) for (conflicts, to_be_inserted) in conflicts_pairs for conflict in
                       conflicts]
    if len(conflicts_pairs) > 0:
        conflicts_list = list()
        for (conflict, to_be_inserted) in conflicts_pairs:
            conflicts_list.append({'toBeInserted': to_be_inserted, 'inKnowledgeGraph': conflict.to_dict()})
        return {'message': 'There are some conflicts in the triple', 'conflicts': conflicts_list}, 409
    return {'message': 'All triples inserted.'}, 200


@kgu_api.route('/triples/', methods=['DELETE'])
def delete_triples():
    """
    Delete triples from knowledge graph.
    ---
    tags:
      - Knowledge Graph Updater
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
        description: Triples were deleted successfully.
        schema:
          id: standard_message
    """
    data = request.get_json()
    if type(data) is list:
        kgu.delete_knowledge(data)
    else:
        kgu.delete_knowledge([data])
    return {'message': 'Triples deleted.'}, 200


@kgu_api.route('/entity/<path:subject>')
def get_entity(subject):
    """
    Returns all triples that has the subject parameter as the subject.
    ---
    tags:
      - Knowledge Graph Updater
    parameters:
      - name: subject
        in: path
        description: subject/entity name (should be in DBpedia format)
        type: string
        required: true
    responses:
      200:
        description: Triples related to entity/subject returned.
        schema:
          id: triples
      404:
        description: No triples found that are related to the entity/subject
        schema:
          id: standard_message
    """
    triples = kgu.get_entity(subject)
    if triples is None:
        return {'message': 'No triples found that are related to ' + subject}, 404
    triples = [triple.to_dict() for triple in kgu.get_entity(subject)]
    return {'triples': triples}, 200


@kgu_api.route('/entity/equals/', methods=['POST'])
def resolve_entity_equality():
    """
    Resolve two entities as the same.
    ---
    tags:
      - Knowledge Graph Updater
    consumes:
      - application/json
    parameters:
      - in: body
        name: two_entities
        schema:
          id: two_entities
          type: object
          properties:
            entity_a:
              type: string
            entity_b:
              type: string
        required: true
    responses:
      200:
        description: Triples were inserted successfully.
        schema:
          id: standard_message
    """
    data = request.get_json()
    kgu.insert_entities_equality(data['entity_a'], data['entity_b'])
    return {'message': 'Entities have been added as the same.'}, 200


class AsyncUpdate(threading.Thread):
    """
    A wrapper for doing update_missed_knowledge asynchronously, so that other endpoints can still be called while this
    operation is running.
    There could only be 1 thread of this running at a time.
    When running, the "updating" flag is set to True, preventing another thread of this to be created.
    """

    def __init__(self, kgu, kg_auto_update=None, extraction_scope=None):
        super().__init__()
        self.kgu = kgu
        self.kg_auto_update = kg_auto_update
        self.extraction_scope = extraction_scope

    def run(self):
        global updating
        updating = True
        try:
            kgu.update_missed_knowledge(kg_auto_update=self.kg_auto_update, extraction_scope=self.extraction_scope)
        except Exception as e:
            logger.error(e)
        updating = False
