#!/usr/bin/env python

import simplejson as json
import time
import random

#from firetower import client
from optparse import OptionParser

import client


FAKE_SIGS = [
    "dfljk3kljljksdjviaaoTEST1ljsdkljdsaslkjdsklj",
    "39jsad vijqerp8 hvasdvasdvTEST2JVIEJ9giaj93aerg",
    "ja394jasdlkvj 3jslajfbTEST3 IJVJ#W(JGSG)"
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
            do_multiply = 1#random.randint(0, 9) # how often to multple 1/10 now.
            sig_multiple = random.randint(2, 100000) # how much to multiple by.
            fake_sig = random.choice(FAKE_SIGS) + str(random.randint(100, 999))
            if do_multiply == 0:
                FAKE_DATA['sig'] = fake_sig * sig_multiple
            else:
                FAKE_DATA['sig'] = fake_sig

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
        default=10000, help='Number of events to send to Firetower.')

    (options, args) = parser.parse_args()

    main = TestClient(options.conf_path)
    main.run(options.num_events)
