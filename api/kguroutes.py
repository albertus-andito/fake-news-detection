from flask import Blueprint, request
from kgupdater import KnowledgeGraphUpdater
import threading
import json

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
    if updating is True:
        return {"message": "Still processing..."}, 202
    return {"message": "Done. Another request can be made."}, 200


@kgu_api.route('/updates/')
def trigger_updates():
    if updating is False:
        async_task = AsyncUpdate(kgu)
        async_task.start()
        return {"message": "Request submitted. Update is processing..."}, 202
    return {"message": "An update is already in process. Check /updates/status for the status"}, 409


@kgu_api.route('/article_triples/insert/', methods=['POST'])
def insert_article_triples():
    data = request.get_json()
    kgu.insert_articles_knowledge(data)
    return {"message": "Triples inserted."}, 200


@kgu_api.route('/article_triples/delete/', methods=['POST'])
def delete_all_article_triples():
    data = request.get_json()
    if type(data) is list:
        for article in data:
            kgu.delete_all_knowledge_from_article(article['source_url'])
    else:
        kgu.delete_all_knowledge_from_article(data['source_url'])
    return {"message": "All triples deleted."}, 200


@kgu_api.route('/article_triples/')
def triples_from_articles():
    return {'pending': kgu.get_all_pending_knowledge()}, 200


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
    def __init__(self, kgu):
        super().__init__()
        self.kgu = kgu

    def run(self):
        global updating
        updating = True
        kgu.update_missed_knowledge()
        updating = False