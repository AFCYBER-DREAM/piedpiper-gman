import json
import os

from attrdict import AttrDict
from flask import Flask

from piedpiper_gman.config import load_config
from piedpiper_gman.gman import GMan
from piedpiper_gman.orm.models import db_init
from piedpiper_gman.util import GManJSONEncoder, SRIConverter, Api


app = Flask('gman')
app.config['RESTFUL_JSON'] = {'cls': GManJSONEncoder}

app.url_map.converters['hash'] = SRIConverter


api = Api(app, catch_all_404s=True)

api.add_resource(GMan,
                 '/gman',
                 '/gman/<uuid:task_id>',
                 '/gman/<uuid:task_id>/<events>')


def app_setup(config_path=None, config=None):
    assert config_path or config, 'No application config specified'
    assert not (config_path and config), 'Specify either a config file or dict'

    if config_path:
        config = load_config(config_path)

    assert isinstance(config, AttrDict), 'Config is not an AttrDict object'

    db_init(config.database)  # Initialize the db (Config.database for config)
    return config


def run_uwsgi(env, start_response):
    # preload config options from environment json string
    config = AttrDict(json.loads(os.environ.get('APP_CONFIG', '{}')))
    assert 'database' in config
    app_setup(config=config)
    return app(env, start_response)


def run_dev(config_path=None, config=None):  # pragma: no cover
    config = app_setup(config_path=config_path)
    app.run(**config.server)
