
from attrdict import AttrDict
from flask import Flask
from flask_restful import Api

from piedpiper_gman.config import load_config
from piedpiper_gman.gman import GMan
from piedpiper_gman.orm.models import db_init


app = Flask(__name__)
api = Api(app)


api.add_resource(GMan,
                 '/gman',
                 '/gman/<uuid:task_id>',
                 '/gman/<uuid:task_id>/<events>')


def run(config_path=None, config=None):
    if config_path:
        Config = load_config(config_path)
    else:
        Config = config

    assert isinstance(Config, AttrDict), 'Config is not an AttrDict object'
    db_init(Config.database)  # Initialize the db (Config.database for config)
    app.run(**Config.server)
