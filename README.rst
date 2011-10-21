=========
Firetower
=========

Firetower is a system designed to be a point of aggregation for errors from a large or distributed system.

One of the key features of Firetower is its ability to classify incoming errors and normalize their counts in a timeseries as to make monitoring and analysis of service errors much easier.

The goal of the project is to bridge the gap in systems analysis between syslog and custom map-reduce style batch analysis systems in terms of performance, accuracy, and ease of setup. It should be noted that this project is still mostly in the prototype stages of development.

The basic form of the error messages are expected to be somewhat backwards compatible with syslog protocol.
See the Syslog RFC_.

.. _RFC: http://tools.ietf.org/html/rfc5424


Basic Workflow
----------------

This is a representation of a basic workflow for Firetower:

.. image::  http://dl.dropbox.com/u/5586906/images/Error_Aggregator_Flow_Log_Redis.png


Installing Redis
------------------

I use the latest stable version of Redis for testing:

::

    wget http://redis.googlecode.com/files/redis-2.2.10.tar.gz
    tar xvf redis-2.2.10.tar.gz
    cd redis-2.2.10/src
    make
    ./redis-server


Installing Firetower
--------------------

I recommend doing all development in a virtualenv

::

    git clone git@github.com:gmcquillan/firetower.git
    virtualenv firetower
    cd firetower
    ./bin/activate


If for some reason python-Levenshtein doesn't install, that's ok. We'll just default to using difflib for string comparisons.

Running Firetower
-----------------

Setup:
If you're using a virtualenv, activate it.

Make sure that your redis server is running on your local machine on the default port (6379).


Running the Demo:


- Turn on the firetower-client:
::

    cd firetower
    . bin/activate
    firetower-client -c configs/config.yaml
    # This should be spitting out JSON to Stdout like this:
    # {'severity': None, 'hostname': 'testmachine', 'syslogtag': 'test', 'sig': 'ToastToast519', 'programname': 'firetower client', 'msg': 'I/O Exception from some file', 'logfacility': 'local1'}

- Turn on the firetower-server:
::

    cd firetower
    . bin/activate
    firetower-server -c configs/config.yaml
    # This will start the classification there will be no output.

- Turn on the web frontend:
::

    cd firetower
    . bin/activate
    firetower-web

- Browse to http://localhost:5000 to see what kind of data is being produced.

- To remove your test data (don't do this on a redis server where you have *ANY* data you care about):
::

    ipython
    >>> import redis
    >>> conn = redis.Redis()
    >>> conn.flushdb()



Running Tests
-------------

We usually just use a test discovery tool called nosetests
Make sure that you have nosetests installed:

::

    pip install nose

::

    cd firetower
    nosetests

Alternatively, you can just run:

::

    python -m unittest discover


TODO
----

- Display/frontend
- Plugable Classifiers
- Installation Scripts
