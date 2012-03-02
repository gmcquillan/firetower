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

    def __init__(self, conf_path):
        self.conf_path = conf_path
        (
            self.redis_host, self.redis_port, self.redis_db, self.queue_key,
            self.alert_time, self.class_thresh, self.timeslices,
            self.archive_time, self.log_file, self.log_level,
            self.imap_user, self.imap_host, self.class_order,
        ) = self.load_conf(file(self.conf_path, 'r'))

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

                { 'redis_host: localhost,
                  'redis_port: 6379,
                  'redis_db: 0,
                  'class_thresh: 0.7,
                  'alert_time': 0.5,
                  'queue_key': 'incoming',
                  'timeslices': [300],
                  'archive_time': 60,
                  'log_file': 'firetower-server.log',
                  'log_level': 1,
                 }
        Returns:
            tuple of queue_key, timeslices, alert_time, redis_host, redis_port,
            archive_time.
        """
        redis_host = conf_dict.get('redis_host', 'localhost')
        redis_port = conf_dict.get('redis_port', 6379)
        redis_db = conf_dict.get('redis_db', 0)
        queue_key = conf_dict.get('queue_key', 'incoming')
        class_thresh = conf_dict.get('class_thresh', 0.5)
        timeslices = conf_dict.get('timeslices', [300])
        alert_time = conf_dict.get('alert_time', 1.0)
        archive_time = conf_dict.get('archive_time', 60)
        log_file = conf_dict.get('log_file', 'firetower-server.log')
        log_level = conf_dict.get('log_level', 1)
        imap_user = conf_dict.get('imap_user', '')
        imap_host = conf_dict.get('imap_host', '')
        class_order = conf_dict.get('class_order', '')

        return (redis_host, redis_port, redis_db, queue_key, alert_time,
                class_thresh, timeslices, archive_time, log_file, log_level,
                imap_user, imap_host, class_order)
