from attrdict import AttrDict
from pytest import raises, fail

from piperci_gman.orm.models import db_init, URIField


def test_bad_config_option():
    db_config = AttrDict({'type': 'postgres', 'uri': ':memory:'})

    with raises(Exception, match='Database type postgres not yet supported'):
        db_init(db_config)
        fail("Failed to raise exception for unsupported db type")


def test_urifield_nonurlparse_db_val():

    uri = URIField()

    with raises(ValueError):
        uri.db_value({'test', 'non-string'})


def test_urifield_nonurlparse_python_val():

    uri = URIField()

    with raises(ValueError):
        uri.python_value({'test', 'non-string'})


def test_urifield_urlparse_python_val():

    uri = URIField()

    uri_parts = uri.python_value('https://example.com')

    uri_parts2 = uri.python_value(uri_parts)

    assert uri_parts2 == uri_parts
