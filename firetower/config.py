#!/usr/bin/env python

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

class Config(object):
    def __init__(self, conf_file):
        self.conf_path = conf_file
        self.self.load_conf(file(self.conf_path, 'r'))

    def load_conf(self, conf_str):
        """Convert string version of configuration to python datastructures."""
        return load(conf_str)

    def check_confg(self, conf_dict):
        """Make sure we have expected keys with some value."""
        pass

