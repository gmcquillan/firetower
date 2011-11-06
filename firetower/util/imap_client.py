import email
import email.parser
import getpass
import imaplib
import json
import time

from optparse import OptionParser

from firetower import config
from firetower.redis_util import Redis

"""maildir_client

This is a module designed at allowing you to bootstrap your
firetower data by importing error emails from a maildir format.
"""

def main():
    parser = OptionParser(usage='usage: firetower options args')
    parser.add_option(
        '-c', '--conf', action='store', dest='conf_path',
         help='Path to YAML configuration file.')
    (options, args) = parser.parse_args()
    conf = config.Config(options.conf_path)

    conn = imaplib.IMAP4_SSL(conf["imap_host"])
    imap_user = conf["imap_user"]
    imap_password = conf.get("imap_password")

    queue = Redis(host=conf.redis_host, port=conf.redis_port)

    processed = 0

    if not imap_password:
        print "Enter email password"
        imap_password = getpass.getpass()

    conn.login(imap_user, imap_password)
    conn.select("Inbox")

    while True:
        _, msg_ids = conn.search(None, "(ALL)")
        msg_ids = msg_ids[0].split()
        if len(msg_ids) == 0:
            time.sleep(0.5)
            continue
        print "Processing %s messages" %len(msg_ids)

        _, msgs = conn.fetch(",".join(msg_ids), '(BODY[])')
        for msg in msgs:
            if not msg or msg == ")":
                continue
            msg_obj = email.message_from_string(msg[1])
            ft_dict = {}
            ft_dict['hostname'] = msg_obj['Received'].split(' ')[1] or '????'
            ft_dict['sig'] = msg_obj.get_payload() or '????'
            ft_dict['date'] = msg_obj["Date"]
            ft_dict['programname'] = 'Maildir Util'

            # We don't huge signatures clogging the classification
            if len(ft_dict['sig']) < 10000 and isinstance(ft_dict['sig'], str):
                queue.push(conf.queue_key, json.dumps(ft_dict))
            processed += 1
            if not processed % 100:
                print "Processed: %s" %processed
        print "Processed: %s" %processed

        for msg_id in msg_ids:
            conn.store(msg_id, '+FLAGS', '\\Deleted')

        conn.expunge()



if __name__ == '__main__':
    main()
