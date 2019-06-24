
from attrdict import AttrDict
import pytest

from piperci_gman.orm.models import db_init
from piperci_gman.app import app as papp
from piperci_gman.gman import GMan
from piperci_gman.util import Api

from flask import current_app


@pytest.fixture
def db():
    db_config = AttrDict({'type': 'sqlite', 'uri': ':memory:'})
    db_init(db_config)


@pytest.fixture
def app(db):  # required by pytest_flask
    return papp


@pytest.fixture
def api():
    return Api(current_app, catch_all_404s=True)


gman_task_create = {
    'run_id': 'create_1',
    'project': 'gman_test_data',
    'caller': 'test_case_create_1',
    'status': 'started',
    'message': 'a normal task creation body'
}


@pytest.fixture
def testtask(api, client):
    def create(json=None):
        json = json if json else gman_task_create
        return client.post(api.url_for(GMan), json=json)
    return create
