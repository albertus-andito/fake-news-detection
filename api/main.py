from flask import Flask
from flasgger import Swagger
from flask_cors import CORS

from kguroutes import kgu_api
from fcroutes import fc_api

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SWAGGER'] = {
    'title': 'Knowledge-Based Fake News Detection API'
}
swagger = Swagger(app)

app.register_blueprint(kgu_api, url_prefix='/kgu')
app.register_blueprint(fc_api, url_prefix='/fc')


if __name__ == '__main__':
    app.run()