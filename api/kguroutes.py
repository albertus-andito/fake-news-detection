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
    responses:
      202:
        description: The update operation is still processing.
      200:
        description: The update operation is done. Another request to update can be made.
    """
    if updating is True:
        return {'message': 'Still processing...'}, 202
    return {'message': 'Done. Another request to update can be made.'}, 200


@kgu_api.route('/updates')
def trigger_updates():
    """
    Triggers an update that will extract triples from stored articles, and add non-conflicting triples to knowledge graph, if specified.
    ---
    parameters:
      - name: auto_update
        in: query
        description: whether the non-conflicting extracted triples are added to the knowledge graph automatically or not.
        required: false
        type: Boolean
        default: false
    responses:
      202:
        description: Request to update is submitted and being processed.
      409:
        description: An update is already in progress. Check /kgu/updates/status for the status of the update.
    """
    if updating is False:
        print(request.args.get('auto_update'))
        auto_update = True if request.args.get('auto_update') == 'true' else False
        async_task = AsyncUpdate(kgu, kg_auto_update=auto_update)
        async_task.start()
        return {'message': 'Request submitted. Update is processing...'}, 202
    return {'message': 'An update is already in progress. Check /kgu/updates/status for the status'}, 409


@kgu_api.route('/article-triples/insert/', methods=['POST'])
def insert_article_triples():
    data = request.get_json()
    kgu.insert_articles_knowledge(data)
    return {"message": "Triples inserted."}, 200


@kgu_api.route('/article-triples/delete/<path:article_url>')
def delete_all_article_triples(article_url):
    """
    Removes all triples of the specified article from the knowledge graph.
    ---
    parameters:
      - name: article_url
        in: path
        description: URL of article whose triples are going to be removed from the knowledge graph.
        type: string
        required: true
    responses:
      200:
        description: All triples from the article have been successfully deleted.
    :param article_url: URL of article whose triples are going to be removed from the knowledge graph.
    :type article_url: str
    :return JSON message
    """
    kgu.delete_all_knowledge_from_article(article_url)
    return {'article_url': article_url, 'message': 'All triples deleted.'}, 200


@kgu_api.route('/article-triples/conflicts', methods=['GET'])
def conflicts_from_article():
    article_url = request.args.get('source')
    conflicts = kgu.get_article_conflicts(article_url)
    if conflicts is None:
        return {'source': article_url, 'message': 'No conflicts found for this article'}, 404
    return {'source': article_url, 'conflicts': conflicts}, 200


@kgu_api.route('/article-triples/conflicts/')
def conflicts_from_articles():
    return {'conflicts': kgu.get_all_article_conflicts()}, 200


@kgu_api.route('/article-triples/pending')
def pending_triples_from_article():
    # TODO
    article_url = request.args.get('source')
    pending = kgu.get_article_pending_knowledge(article_url)
    if pending is None:
        return {'source': article_url, 'message': 'No pending triples (to be added to the knowledge graph) found for '
                                                  'this article'}, 404
    return {'source': article_url, 'pending': kgu.get_article_pending_knowledge(article_url)}


@kgu_api.route('/article-triples/pending/')
def pending_triples_from_articles():
    return {'pending': kgu.get_all_pending_knowledge()}, 200


@kgu_api.route('/article-triples')
def triples_from_article():
    article_url = request.args.get('source')
    triples = kgu.get_article_knowledge(article_url)
    if triples is None:
        return {'source': article_url, 'message': 'Triples haven\'t been extracted from this article. Please call the '
                                                  '/kgu/updates/ endpoint.'}, 404
    return {'source': article_url, 'triples': triples}, 200


@kgu_api.route('/article-triples/')
def triples_from_articles():
    return {'triples': kgu.get_all_articles_knowledge()}, 200


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
        if kg_auto_update is not None:
            self.kg_auto_update = kg_auto_update
        else:
            self.kg_auto_update = False

    def run(self):
        global updating
        updating = True
        print(self.kg_auto_update)
        kgu.update_missed_knowledge(kg_auto_update=self.kg_auto_update)
        updating = False
