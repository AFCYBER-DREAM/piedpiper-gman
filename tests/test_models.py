from attrdict import AttrDict
from pytest import raises, fail

from piedpiper_gman.orm.models import db_init


def test_bad_config_option():
    db_config = AttrDict({'type': 'postgres', 'uri': ':memory:'})

    with raises(Exception, match='Database type postgres not yet supported'):
        db_init(db_config)
        fail("Failed to raise exception for unsupported db type")
