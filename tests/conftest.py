
from attrdict import AttrDict
import pytest

from piedpiper_gman.orm.models import db_init
from piedpiper_gman.app import app as papp

from flask import current_app
from flask_restful import Api


@pytest.fixture
def db():
    db_config = AttrDict({'type': 'sqlite', 'uri': ':memory:'})

    db_init(db_config)


@pytest.fixture
def app(db):  # required by pytest_flask
    return papp


@pytest.fixture
def api():
    return Api(current_app)
