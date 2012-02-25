#!/usr/bin/env python

import simplejson as json

from optparse import OptionParser

from firetower import config
from firetower import client
from firetower.util.pykafka import kafka


class KafkaClient(client.Client):

    def _check_offset(self):
        """Check if there's an offset in Redis for us to start."""
        pass

    def _set_offset(self):
        """Set a new offset in Redis."""
        pass

    def collect(self, topic, host='localhost', port=9092):
        """Accept, process, emit logline data to redis.

        Args:
            topic: str, name of topic to subscribe to.
            host: str, hostname where kafka service lives.
            post: int, TCP port to connect.
        """
        consumer = kafka.consumer.Consumer(topic)
        for message in consumer.loop():
            event = {}
            try:
                event = json.loads(message.__str__())
            except ValueError, e:
                pass

            self.emit(event)

def main():
    parser = OptionParser(
            usage='usage: kafkacollector -c <config> -H <hostname> -p <port> -t <topic>')
    parser.add_option(
            '-c', '--conf', action='store', dest='conf_path',
            help='Path to YAML configuration file.')
    parser.add_option(
            '-p', '--path', action='store', dest='log_path',
            help='Path to watch for logfile changes.')
    parser.add_option(
            '-H', '--host', action='store', dest='kafka_host',
            help='Kafka host to connect with.')
    parser.add_option(
            '-p', '--port', action='store', dest='kafka_port',
            help='Kafka port.')
    parser.add_option(
            '-t', '--topic', action='store', dest='kafka_topic',
            help='Kafka Topic to consume from.')

    (options, args) = parser.parse_args()

    client = KafkaClient(options.conf_path)
    client.connect
    client.collect(options.kafka_topic)

if __name__ == '__main__':
    main()
