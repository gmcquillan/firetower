tracebacks = [
    """Traceback (most recent call last):
     File "/lib/python2.6/site-packages/django_some_really_cool_module-py2.6.egg/module/class.py", line 99, in get_response
       response = callback(request, *callback_args, **callback_kwargs)
     File "/mnt/services/airship/lib/python2.6/site-packages/Django-1.1.3-py2.6.egg/django/views/decorators/vary.py", line 21, in inner_func
       response = func(*args, **kwargs)
     File ""/lib/python2.6/site-packages/django_some_really_cool_module-py2.6.egg/module/__init__.py", line 117, in __call__
       result = resource.Resource.__call__(self, request, *args, **kwargs)
     File ""/lib/python2.6/site-packages/django_some_really_cool_module-py2.6.egg/module/class.py", line 21, in inner_func
       response = func(*args, **kwargs)
     File "/lib/python2.6/site-packages/django_some_really_cool_module-py2.6.egg/module/class.py", line 166, in __call__
       result = meth(request, *args, **kwargs)
     File "api/things.py", line 34, in wrap
       return handler_method(self, request, *args, **kwargs)
     File "api/other_things.py", line 122, in wrapped_f
       return f(self, request, data, *args, **kwargs)
     File "api/endpoints/something.py", line 173, in EXECUTE
       something.do_something)
     File "/lib/python2.6/site-packages/django_some_really_cool_module-py2.6.egg/module/class.py", line 194, in enqueue_task
       thingy = queue_obj.open_connection(task_thingy)
     File "/lib/python2.6/site-packages/django_some_other_really_cool_module-py2.6.egg/module/class.py", line 140, in open_connection
       return queue.Connection(settings.host, settings.port)
     File "/lib/python2.6/site-packages/another_thing-2.6.egg/module/class.py"
       SocketError.wrap(self._socket.connect, (self.host, self.port))
     File "/lib/python2.6/site-packages/django_some_really_cool_module-py2.6.egg/module/class.py", line 43, in do_something
       raise SocketError(e)
    SocketError: [Errno 110] Connection timed out""",
    """me.prettyprint.hector.api.exceptions.HTimedOutException: org.apache.thrift.transport.TTransportException: java.net.SocketTimeoutException: Read timed out
        at me.prettyprint.cassandra.service.ExceptionsTranslatorImpl.translate(ExceptionsTranslatorImpl.java:35)
        at me.prettyprint.cassandra.service.KeyspaceServiceImpl$5.execute(KeyspaceServiceImpl.java:223)
        at me.prettyprint.cassandra.service.KeyspaceServiceImpl$5.execute(KeyspaceServiceImpl.java:206)
        at me.prettyprint.cassandra.service.Operation.executeAndSetResult(Operation.java:101)
        at me.prettyprint.cassandra.connection.HConnectionManager.operateWithFailover(HConnectionManager.java:224)
        at me.prettyprint.cassandra.service.KeyspaceServiceImpl.operateWithFailover(KeyspaceServiceImpl.java:129)
        at me.prettyprint.cassandra.service.KeyspaceServiceImpl.getSlice(KeyspaceServiceImpl.java:227)
        at me.prettyprint.cassandra.model.thrift.ThriftSliceQuery$1.doInKeyspace(ThriftSliceQuery.java:53)
        at me.prettyprint.cassandra.model.thrift.ThriftSliceQuery$1.doInKeyspace(ThriftSliceQuery.java:49)
        at me.prettyprint.cassandra.model.KeyspaceOperationCallback.doInKeyspaceAndMeasure(KeyspaceOperationCallback.java:20)
        at me.prettyprint.cassandra.model.ExecutingKeyspace.doExecute(ExecutingKeyspace.java:85)
        at me.prettyprint.cassandra.model.thrift.ThriftSliceQuery.execute(ThriftSliceQuery.java:48)
        at com.urbanairship.helib.UACassandra.get(UACassandra.java:82)
        at com.urbanairship.helib.UACassandra.get(UACassandra.java:91)
        at com.urbanairship.helib.models.APID.get(APID.java:52)
        at com.urbanairship.helib.tasks.CheckRegistration.processRegistration(CheckRegistration.java:135)
        at com.urbanairship.helib.tasks.CheckRegistration.run(CheckRegistration.java:83)
        at com.urbanairship.octobot.TaskExecutor.execute(TaskExecutor.java:19)
        at com.urbanairship.octobot.QueueConsumer.invokeTask(QueueConsumer.java:197)
        at com.urbanairship.octobot.QueueConsumer.consumeFromBeanstalk(QueueConsumer.java:106)
        at com.urbanairship.octobot.QueueConsumer.run(QueueConsumer.java:49)
        at java.lang.Thread.run(Thread.java:662)
    Caused by: org.apache.thrift.transport.TTransportException: java.net.SocketTimeoutException: Read timed out
        at org.apache.thrift.transport.TIOStreamTransport.read(TIOStreamTransport.java:129)
        at org.apache.thrift.transport.TTransport.readAll(TTransport.java:84)
        at org.apache.thrift.transport.TFramedTransport.readFrame(TFramedTransport.java:129)
        at org.apache.thrift.transport.TFramedTransport.read(TFramedTransport.java:101)
        at org.apache.thrift.transport.TTransport.readAll(TTransport.java:84)
        at org.apache.thrift.protocol.TBinaryProtocol.readAll(TBinaryProtocol.java:378)
        at org.apache.thrift.protocol.TBinaryProtocol.readI32(TBinaryProtocol.java:297)
        at org.apache.thrift.protocol.TBinaryProtocol.readMessageBegin(TBinaryProtocol.java:204)
        at org.apache.cassandra.thrift.Cassandra$Client.recv_get_slice(Cassandra.java:530)
        at org.apache.cassandra.thrift.Cassandra$Client.get_slice(Cassandra.java:512)
        at me.prettyprint.cassandra.service.KeyspaceServiceImpl$5.execute(KeyspaceServiceImpl.java:211)
        ... 20 more
    Caused by: java.net.SocketTimeoutException: Read timed out
        at java.net.SocketInputStream.socketRead0(Native Method)
        at java.net.SocketInputStream.read(SocketInputStream.java:129)
        at java.io.BufferedInputStream.fill(BufferedInputStream.java:218)
        at java.io.BufferedInputStream.read1(BufferedInputStream.java:258)
        at java.io.BufferedInputStream.read(BufferedInputStream.java:317)
        at org.apache.thrift.transport.TIOStreamTransport.read(TIOStreamTransport.java:127)
        ... 30 more""",
]
