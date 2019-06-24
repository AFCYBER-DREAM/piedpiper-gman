#!/usr/bin/env python3

from os import path

from piperci_gman.app import run_dev


if __name__ == '__main__':
    run_dev(config_path=path.realpath('./config.yml'))
