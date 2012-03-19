import email
import email.parser
import getpass
import imaplib
import json
import time

from optparse import OptionParser

from firetower import config
from firetower import redis_util

"""maildir_client

This is a module designed at allowing you to bootstrap your
firetower data by importing error emails from a maildir format.
"""

def main():
    parser = OptionParser(usage='usage: firetower options args')
    parser.add_option(
        '-c', '--conf', action='store', dest='conf_path',
         help='Path to YAML configuration file.',
    )
    parser.add_option(
        '-d', dest='clear_firstrun', action="store_true", default=False,
        help='Clear backed up emails on first run'
    )
    parser.add_option(
        '-p', dest='imap_password', action="store_true", default=False,
        help='IMAP password.'
    )
    (options, args) = parser.parse_args()
    conf = config.Config(options.conf_path)

    conn = imaplib.IMAP4_SSL(conf.imap_host)
    imap_user = conf.imap_user
    imap_password = options.user_pass

    queue = redis_util.get_redis_conn(
        host=conf.redis_host, port=conf.redis_port, redis_db=conf.redis_db)

    processed = 0

    if not imap_password:
        print "Enter email password"
        imap_password = getpass.getpass()

    conn.login(imap_user, imap_password)
    conn.select("Inbox")

    first_run = True

    while True:
        _, msg_ids = conn.search(None, "(ALL)")
        msg_ids = msg_ids[0].split()
        if len(msg_ids) == 0:
            time.sleep(0.5)
            if first_run:
                first_run = False
            continue
        print "Processing %s messages" %len(msg_ids)

        id_batches = []
        # split the ids into batches of 1000
        count = 0
        split = 1000
        while count < len(msg_ids):
            id_batches.append(msg_ids[count:count+split])
            count += split

        for id_batch in id_batches:
            if options.clear_firstrun and first_run:
                first_run = False
                break

            _, msgs = conn.fetch(",".join(id_batch), '(BODY[])')
            for msg in msgs:
                if not msg or msg == ")":
                    continue
                msg_obj = email.message_from_string(msg[1])
                ft_dict = {}
                ft_dict['hostname'] = msg_obj['Received'].split(' ')[1] if msg_obj['Received'] else '????'
                ft_dict['sig'] = msg_obj.get_payload() or '????'
                ft_dict['date'] = msg_obj["Date"]
                ft_dict['programname'] = 'Maildir Util'

                # We don't huge signatures clogging the classification
                if len(ft_dict['sig']) < 10000 and isinstance(ft_dict['sig'], str):
                    queue.lpush(conf.queue_key, json.dumps(ft_dict))
                processed += 1
                if not processed % 100:
                    print "Processed: %s" %processed

        for msg_id in msg_ids:
            conn.store(msg_id, '+FLAGS', '\\Deleted')
        print "Processed: %s" %processed



        conn.expunge()



if __name__ == '__main__':
    main()
