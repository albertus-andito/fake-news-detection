from flask import Blueprint

fc_api = Blueprint('fc_api', __name__)


@fc_api.route('/')
def hello_world():
    return 'Hello Fact Checker'
