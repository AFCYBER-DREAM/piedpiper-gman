import uuid
import json

from piedpiper_gman.util import GManJSONEncoder
from pytest import raises


def test_jsonencoder_uuid():

    json.dumps({'uuid': uuid.uuid4()}, cls=GManJSONEncoder)


def test_jsonencoder_not_uuid():
    class SomethingNotSupported(object):
        propx = None

    with raises(TypeError):
        json.dumps({'notsupported': SomethingNotSupported()}, cls=GManJSONEncoder)
