import simplejson as json
import random

from optparse import OptionParser

import config
from redis_util import Redis

FAKE_SIGS = ["Test Error, Exception Blah",
             "I'm broken!",
             "Etc.",
             "Yup!"
]
FAKE_DATA = {"hostname": "testmachine",
             "msg": "I/O Exception from some file",
             "logfacility": None,
             "syslogtag": None,
             "programname": None,
             "severity": None}


class Client(object):
    """Main loop."""

    def run(self, conf):
        queue = Redis(host=conf.host, port=conf.port)
        print queue.conn.keys()
        for i in xrange(0, 5):
            try:
                # Semi-randomly seed the 'sig' key in our fake errors
                FAKE_DATA['sig'] = random.choice(FAKE_SIGS)
                encoded = json.dumps(FAKE_DATA)
                err = queue.push(conf.queue_key, encoded)
            except:
                print "Something went wrong storing value from redis"


def main():
    parser = OptionParser(usage='usage: firetower options args')
    parser.add_option(
        '--conf', action='store', dest='conf_path',
         help='Path to YAML configuration file.')

    (options, args) = parser.parse_args()

    if len(args) > 1:
        parser.error('Please supply some arguments')

    conf = config.Config(options.conf_path)

    main = Client()
    main.run(conf)
