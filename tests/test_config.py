from pytest import raises

from piedpiper_gman.config import load_config


def test_bad_config_path():
    with raises(IOError):
        load_config('nopath')


def test_good_config_path():

    load_config('config.yml')
