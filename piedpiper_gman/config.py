from os import path

import yaml
from attrdict import AttrDict


def load_config(config_file):
    file = path.abspath(path.expanduser(path.expandvars(config_file)))
    with open(file) as conf_file:
        return AttrDict(yaml.safe_load(conf_file))
