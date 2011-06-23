#!/usr/bin/env python

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

class ConfigError(Exception):
    pass

class ErrorSigIssue(ConfigError):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)

class Config(object):
    def __init__(self, conf_file):
        self.conf_path = conf_file
        self.queue_key, self.alert_time, self.timeslices, self.error_signatures = \
                self.load_conf(file(self.conf_path, 'r'))

    def load_conf(self, conf_str):
        """Convert string version of configuration to python datastructures."""
        return self.check_config(load(conf_str))

    def check_config(self, conf_dict):
        """Make sure we have expected keys with some value."""

        queue_key = conf_dict.get('queue_key', 'incoming')
        timeslices = conf_dict.get('timeslices', [300])
        alert_time = conf_dict.get('alert_time', 1.0)

        if 'error_signatures' not in conf_dict or not conf_dict['error_signatures']:
            raise ErrorSigIssue('No Error Signatures Defined in Conf')

        error_signatures = conf_dict['error_signatures']

        return (queue_key, alert_time, timeslices, error_signatures)
