#!/usr/bin/env python

import random
import time

import json

import client
import example_client

from optparse import OptionParser

import firetower
from firetower import config
import util.pykafka.kafka.producer as producer
import util.pykafka.kafka.message as message


class KafkaProducer(object):

    def __init__ (self, topic, host, port):
        self.producer = producer.Producer(topic, host=host, port=port)

    def send (self, data):
        """Sends string data to Kafka topic."""
        print "sending: %s" % data
        msg  = message.Message(data)
        self.producer.send(msg)

    def run (self, num_events):
        for i in xrange(0, num_events):
            sig_multiple = random.randint(2,1000)
            fake_sig = random.choice(example_client.FAKE_SIGS) + str(random.randint(100, 999999))
            example_client.FAKE_DATA['sig'] = fake_sig

            encoded = json.dumps(example_client.FAKE_DATA)
            self.send(encoded)
            if not i % 100:
                time.sleep(random.random())
            else:
                print i


def main():
    parser = OptionParser(
            usage='usage: kafkaproducer -c <config> -H <hostname> -p <port> -t <topic>')
    parser.add_option(
            '-c', '--conf', action='store', dest='conf_path',
            help='Path to YAML configuration file.')
    parser.add_option(
            '-H', '--host', action='store', dest='kafka_host',
            help='Kafka host to connect with.')
    parser.add_option(
            '-p', '--port', action='store', dest='kafka_port', type='int',
            help='Kafka port.')
    parser.add_option(
            '-t', '--topic', action='store', dest='kafka_topic',
            help='Kafka Topic to consume from.')
    parser.add_option(
            '-n', '--num', action='store', dest='num_events', type='int',
            help='Number of fake events to fire into kafka.')

    (options, args) = parser.parse_args()

    print options.kafka_topic, options.kafka_host, options.kafka_port

    client = KafkaProducer(options.kafka_topic, options.kafka_host, options.kafka_port)
    client.run(options.num_events)

if __name__ == '__main__':
    main()
