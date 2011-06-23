import redis_util
import simplejson as json
import random

queue_key = 'incoming'

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


class ClientExample(object):
    """Main loop."""

    def run(self):
        queue = redis_util.Redis()
        for i in xrange(0, 10000):
            try:
                # Semi-randomly seed the 'sig' key in our fake errors
                FAKE_DATA['sig'] = random.choice(FAKE_SIGS)
                encoded = json.dumps(FAKE_DATA)
                err = queue.push(queue_key, encoded)
            except:
                print "Something went wrong storing value from redis"


def main():
    main = ClientExample()
    main.run()
