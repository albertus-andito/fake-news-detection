from flask import Flask
from flasgger import Swagger

from kguroutes import kgu_api
from fcroutes import fc_api

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Knowledge-Based Fake News Detection API'
}
swagger = Swagger(app)

app.register_blueprint(kgu_api, url_prefix='/kgu')
app.register_blueprint(fc_api, url_prefix='/fc')


if __name__ == '__main__':
    app.run()