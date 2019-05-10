from os import path

from attrdict import AttrDict
from flask import Flask
from flask_restful import Resource, Api

import yaml

from piedpiper_gman.config import Config
from piedpiper_gman.gman import GMan
from piedpiper_gman.orm.models import db_init

app = Flask(__name__)
api = Api(app)

api.add_resource(GMan, '/gman', '/gman/<uuid:task_id>')

if __name__ == '__main__':
    db_init()  # Initialize the db (Config.database for config)
    app.run(**Config.server)
