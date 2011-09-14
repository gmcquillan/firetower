#!/usr/bin/env python

from yaml import load

class ConfigError(Exception):
    pass


class ErrorSigIssue(ConfigError):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class Config(object):
    """Configuraiton Object - read and store conf values."""

    def __init__(self, conf_file):
        self.conf_path = conf_file
        self.redis_host, self.redis_port, self.queue_key, self.alert_time,  \
        self.class_thresh, self.timeslices, self.error_signatures = \
                self.load_conf(file(self.conf_path, 'r'))

    def load_conf(self, conf_str):
        """Convert string version of configuration to python datastructures.

        Args:
            conf_str: str, yaml formatted string.
        Returns:
            output from check_config, a tuple (queue_key, timeslices,
            alert_time, error_signatures).
        """
        return self.check_config(load(conf_str))

    def check_config(self, conf_dict):
        """Make sure we have expected keys with some value.

        Args:
            conf_dict: a dict which contains all of the configuraiton
            parameters for alerting and classification. It should
            look similar to this:

                 {'error_signatures': {
                    'Test Error': {
                        'alert_thresholds': {'high': 1000},
                        'signatures': {'sig': 'Test Error','threshold': 0.5}}},
                  'alert_time': 0.5,
                  'queue_key': 'incoming',
                  'timeslices': [300]}
        Returns:
            tuple of queue_key, timeslices, alert_time, error_signatures
        """
        redis_host = conf_dict.get('redis_host', 'localhost')
        redis_port = conf_dict.get('redis_port', 6379)
        queue_key = conf_dict.get('queue_key', 'incoming')
        class_thresh = conf_dict.get('class_thresh', 0.5)
        timeslices = conf_dict.get('timeslices', [300])
        alert_time = conf_dict.get('alert_time', 1.0)

        if 'error_signatures' not in conf_dict or not conf_dict[
                'error_signatures']:
            raise ErrorSigIssue('No Error Signatures Defined in Conf')

        error_signatures = conf_dict['error_signatures']

        return (redis_host, redis_port, queue_key, alert_time,
                class_thresh, timeslices, error_signatures)
