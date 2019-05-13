#!/usr/bin/env python3

from os import path

from piedpiper_gman.app import run


if __name__ == '__main__':
    run(config_path=path.realpath('./config.yml'))
