import pytest

from piperci_gman.app import app_setup, run_uwsgi

from werkzeug.wsgi import ClosingIterator

from attrdict import AttrDict


@pytest.fixture
def wsgi_env():
    return {'REQUEST_METHOD': 'GET',
            'REQUEST_URI': '/gman/cad524e5-6975-45f7-941b-9435a5a2bfe1/tasks',
            'PATH_INFO': '/gman/cad524e5-6975-45f7-941b-9435a5a2bfe1/tasks',
            'QUERY_STRING': '', 'SERVER_PROTOCOL': 'HTTP/1.1', 'SCRIPT_NAME': '',
            'SERVER_NAME': 'Nicks-MBP-2.router', 'SERVER_PORT': '8080',
            'UWSGI_ROUTER': 'http',
            'REMOTE_ADDR': '127.0.0.1',
            'REMOTE_PORT': '59595',
            'HTTP_HOST': 'localhost:8080',
            'HTTP_USER_AGENT': 'curl/7.54.0',
            'HTTP_ACCEPT': '*/*',
            'wsgi.input': None,
            'wsgi.file_wrapper': None,
            'wsgi.version': (1, 0),
            'wsgi.errors': None,
            'wsgi.run_once': False,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.url_scheme': 'http',
            'uwsgi.version': b'2.0.18',
            'uwsgi.node': b'Test'}


def test_app_setup_bad_conf():
    with pytest.raises(AssertionError) as e:
        app_setup(config={'x'})

    assert 'Config is not an AttrDict object' in str(e._excinfo)


def test_app_setup_no_conf():
    with pytest.raises(AssertionError) as e:
        app_setup()

    assert 'No application config specified' in str(e._excinfo)


def test_app_setup_both_configs():
    with pytest.raises(AssertionError) as e:
        app_setup(config_path='config.yml', config=AttrDict({'key': 'test'}))

        assert 'Specify either a config file or dict' in str(e._excinfo)


def test_app_config_file():
    config = app_setup('config.yml')
    assert isinstance(config, AttrDict), 'config from app_setup is not an AttrDict'


def test_uwsgi(monkeypatch, wsgi_env):

    monkeypatch.setenv('APP_CONFIG',
                       '{"database": {"type": "sqlite", "uri": "gman.db"}}')

    def stub(*args, **kwargs):
        assert len(args) or len(kwargs)

    werkz = run_uwsgi(wsgi_env, stub)
    assert isinstance(werkz, ClosingIterator), ('returned wsgi interface is not the '
                                                'right type')
