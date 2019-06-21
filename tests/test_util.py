import uuid
import json
import pytest
from piedpiper import sri

from piedpiper_gman.util import (GManJSONEncoder, Api)
from piedpiper_gman.gman import GMan
from piedpiper_gman.artman import ArtMan
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

    resp = client.get('/artifact/sri/mal-formedsri')

    assert resp.status_code == 404


def test_handle_error_500(monkeypatch, client):

    class DumbyError(Exception):
        def __init__(self, *args, **kwargs):
            self.code = 500

    err = Api.handle_error

    def error_wrapper(self, e):
        return err(self, DumbyError())

    monkeypatch.setattr(Api, 'handle_error', error_wrapper)

    assert client.get('/artifact/sri/mal-formedsri').status_code == 500


hashes = [
    sri.sri_to_hash('sha256-vFatceyWaE9Aks3N9ouRUtba1mwrIHdEVLti88atIvc='),
    'sha256-vFatceyWaE9Aks3N9ouRUtba1mwrIHdEVLti88atIvc='
]


@pytest.mark.parametrize('hash', hashes)
def test_to_url_sri(client, api, hash):
    url = api.url_for(ArtMan, sri=hash)

    assert 'c2hhMjU2LXZGYXRjZXlXYUU5QWtzM045b3VSVXRiYTFtd3JJSGRFVkx0aTg4YXRJdmM9' in url


def test_to_url_sri_error(client, api):
    url = api.url_for(ArtMan, sri={'asdfasdfsad'})
    assert 'sri=' in url


def test_unhandled_error(client, api, monkeypatch):
    h_errors = Api.handle_error

    def handle_error_stub(self, e):
        e = ValueError('testing a non .status_code error that is not TypeError')

        return h_errors(self, e)

    monkeypatch.setattr('piedpiper_gman.util.Api.handle_error', handle_error_stub)

    resp = client.put(api.url_for(GMan))

    assert resp.status_code == 500
