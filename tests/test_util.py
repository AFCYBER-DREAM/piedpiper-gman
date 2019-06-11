import uuid
import json

from piedpiper import sri

from piedpiper_gman.util import (GManJSONEncoder, Api)
from pytest import raises


def test_jsonencoder_uuid():

    json.dumps({'uuid': uuid.uuid4()}, cls=GManJSONEncoder)


def test_jsonencoder_default_encoder():

    j = json.dumps({'uuid': 'stringxyz'}, cls=GManJSONEncoder)

    assert json.loads(j)['uuid'] == 'stringxyz'


def test_jsonencoder_hash():

    j = json.dumps(
        {'uuid':
         sri.sri_to_hash('sha256-sCDaaxdshXhK4sA/v4dMHiMWhtGyQwA1fP8PgrN0O5g=')},
        cls=GManJSONEncoder)

    assert 'sha256-sCDaaxdshXhK4sA/v4dMHiMWhtGyQwA1fP8PgrN0O5g=' in j


def test_jsonencoder_not_uuid():
    class SomethingNotSupported(object):
        propx = None

    with raises(TypeError):
        json.dumps({'notsupported': SomethingNotSupported()}, cls=GManJSONEncoder)


def test_handle_error_404(client):

    resp = client.get('/gman/sri/mal-formedsri')

    assert resp.status_code == 404


def test_handle_error_500(monkeypatch, client):

    class DumbyError(Exception):
        def __init__(self, *args, **kwargs):
            self.code = 500

    err = Api.handle_error

    def error_wrapper(self, e):
        return err(self, DumbyError())

    monkeypatch.setattr(Api, 'handle_error', error_wrapper)

    assert client.get('/gman/sri/mal-formedsri').status_code == 500
