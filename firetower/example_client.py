#!/usr/bin/env python

import simplejson as json
import time
import random

#from firetower import client
from optparse import OptionParser

import client


FAKE_SIGS = [
'Test Exception', 'Another Random Error', 'Banannas', 'ToastToast'
]

FAKE_DATA = {'hostname': 'testmachine',
             'msg': 'I/O Exception from some file',
             'logfacility': 'local1',
             'syslogtag': 'test',
             'programname': 'firetower client',
             'severity': None}

class TestClient(client.Client):
    """Test Client emits random permutations on signatures to Firetower."""

    def run(self, num_events):
        for i in xrange(0, num_events):
            # Semi-randomly seed the 'sig' key in our fake errors
            FAKE_DATA['sig'] = random.choice(FAKE_SIGS) + str(random.randint(100, 999))
            encoded = json.dumps(FAKE_DATA)
            self.emit(encoded)
            if not i % 100:
                time.sleep(random.random())


def main():
    parser = OptionParser(usage='usage: firetower-client -c <path to conf>')
    parser.add_option(
        '-c', '--conf', action='store', dest='conf_path',
         help='Path to YAML configuration file.')

    parser.add_option(
        '-n', '--num', action='store', dest='num_events', type='int',
        default=1000, help='Number of events to send to Firetower.')

    (options, args) = parser.parse_args()

    main = TestClient(options.conf_path)
    main.run(options.num_events)
