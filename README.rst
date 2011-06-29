Installing Redis
----------------

I use the latest stable version of Redis for testing: 

    wget http://redis.googlecode.com/files/redis-2.2.10.tar.gz
    tar xvf redis-2.2.10.tar.gz
    cd redis-2.2.10/src
    make
    ./redis-server

Installing Firetower
--------------------

I recommend doing all development in a virtualenv

    git clone git@github.com:gmcquillan/firetower.git
    virtualenv firetower
    cd firetower
    ./bin/activate
    pip install python-Levenshtein

If for some reason python-Levenshtein doesn't install, that's ok. We'll just default to using difflib for string comparisons.

Running Firetower
-----------------

Setup:
If you're using a virtualenv, activate it.

Make sure that your redis server is running on your local machine on the default port (6379).


Running the Demo:
If you want to populate data into the Redis queue, just run the client_example.py. It will populate 10k 
fake errors into the queue (with one of four random signatures).

Then, if you want to run the aggregator/classifcation daemon, run firetower.py. It will pull data out of the 'incoming' redis key, classify it, and
write normalized count data into a key named after the error signature you're tracking.


TODO
----

- Display/frontend
- Plugable Classifiers 
- Installation Scripts

