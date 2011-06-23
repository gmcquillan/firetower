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
