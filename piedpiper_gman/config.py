from os import path

import yaml
from attrdict import AttrDict


def load_config(config_file):
    file = path.abspath(path.expanduser(path.expandvars(config_file)))
    with open(config_file) as conf_file:
        return AttrDict(yaml.load(conf_file))

Config = load_config('./config.yml')
