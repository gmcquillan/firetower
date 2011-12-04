#!/usr/bin/env python

import json

from optparse import OptionParser

from firetower import config
from firetower import client
from firetower.util import log_watcher


class LocalLogClient(client.Client):

    #TODO(gavin): This isn't getting called as expected.
    def collect(self, file, lines):
        """Accept, process, emit logline data to redis.

        Args:
            file: str, name of file the lines come from.
            lines: list of str, data from the most recent buffer read.
        """
        event = {}
        for line in lines:
            event['hostname'] = 'localhost'
            event['sig'] = line
            event['filename'] = file
            event['programname'] = 'Firetower local log client'
            self.emit(json.dumps(event))


def main():
    parser = OptionParser(
            usage='usage: logcollector -c <config> -p <path> -s <suffix>')
    parser.add_option(
            '-c', '--conf', action='store', dest='conf_path',
            help='Path to YAML configuration file.')
    parser.add_option(
            '-p', '--path', action='store', dest='log_path',
            help='Path to watch for logfile changes.')

    (options, args) = parser.parse_args()
    conf = config.Config(options.conf_path)

    client = LocalLogClient(conf)
    print "about to get dirty with logwatcher"
    logwatcher = log_watcher.LogWatcher(options.log_path, client.collect)
    logwatcher.loop()

