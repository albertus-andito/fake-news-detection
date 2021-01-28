from flask import Flask
from kguroutes import kgu_api
from fcroutes import fc_api

app = Flask(__name__)

app.register_blueprint(kgu_api, url_prefix='/kgu')
app.register_blueprint(fc_api, url_prefix='/fc')


if __name__ == '__main__':
    app.run()