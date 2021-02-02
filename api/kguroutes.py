from flask import Blueprint, request
from kgupdater import KnowledgeGraphUpdater
import threading

kgu = KnowledgeGraphUpdater()

kgu_api = Blueprint('kgu_api', __name__)


@kgu_api.route('/')
def hello_world():
    return 'Hello, World!'


@kgu_api.route('/test')
def hello_test():
    if False:
        return kgu.test(), 201

    return "bb", 300


updating = False


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
        print(auto_update)
        async_task = AsyncUpdate(kgu, kg_auto_update=auto_update)
        async_task.start()
        return {'message': 'Request submitted. Update is processing...'}, 202
    return {'message': 'An update is already in progress. Check /kgu/updates/status for the status'}, 409


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
            $ref: '#/definitions/triples'
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
          $ref: '#/definitions/triples'
      404:
        description: No pending triples for the specified article are not found.
        schema:
          id: article_url_with_message
    """
    # TODO
    pending = kgu.get_article_pending_knowledge(source)
    if pending is None:
        return {'source': source, 'message': 'No pending triples (to be added to the knowledge graph) found for '
                                             'this article'}, 404
    return {'source': source, 'triples': pending}


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
                $ref: '#/definitions/triples'
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
      triples:
        properties:
          source:
            type: string
          triples:
            type: array
            description: array of triples extracted from the article
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
          $ref: '#/definitions/triples'
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
                $ref: '#/definitions/triples'
        """
    # TODO: add pagination
    return {'all_triples': kgu.get_all_articles_knowledge()}, 200


@kgu_api.route('/triples/confirm/', methods=['POST'])
def force_insert_triples():
    data = request.get_json()
    if type(data) is list:
        for triple in data:
            kgu.insert_knowledge(triple, check_conflict=False)
    else:
        kgu.insert_knowledge(data, check_conflict=False)
    return {'message': 'All triples inserted.'}, 200


@kgu_api.route('/triples/', methods=['POST'])
def insert_triples():
    data = request.get_json()
    conflicts = []
    if type(data) is list:
        conflicts = [conflict for conflict in (kgu.insert_knowledge(triple, check_conflict=True) for triple in data)
                     if conflict is not None]
    else:
        conflict = kgu.insert_knowledge(data, check_conflict=True)
        if conflict is not None:
            conflicts = [conflict]
    if len(conflicts) > 0:
        conflicts = [[triple.to_dict() for triple in conflict] for conflict in conflicts]
        return {'message': 'There are some conflicts in the triple', 'conflicts': conflicts}, 409
    return {'message': 'All triples inserted.'}, 200


@kgu_api.route('/triples/', methods=['DELETE'])
def delete_triples():
    data = request.get_json()
    if type(data) is list:
        kgu.delete_knowledge(data)
    else:
        kgu.delete_knowledge([data])
    return {'message': 'Triples deleted.'}, 200


@kgu_api.route('/entity/<subject>')
def get_entity(subject):
    triples = [triple.to_dict() for triple in kgu.get_entity(subject)]
    return {'triples': triples}, 200


class AsyncUpdate(threading.Thread):
    """
    A wrapper for doing update_missed_knowledge asynchronously, so that other endpoints can still be called while this
    operation is running.
    There could only be 1 thread of this running at a time.
    When running, the "updating" flag is set to True, preventing another thread of this to be created.
    """

    def __init__(self, kgu, kg_auto_update=None):
        super().__init__()
        self.kgu = kgu
        self.kg_auto_update = kg_auto_update

    def run(self):
        global updating
        updating = True
        kgu.update_missed_knowledge(kg_auto_update=self.kg_auto_update)
        updating = False
