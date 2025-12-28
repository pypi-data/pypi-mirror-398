Configuration
=============

All configuration can be done by adding configuration files.

Configurable options
--------------------

Below, we describe client section and the parameters available within it.


[client]
--------

These parameters control the Client. The client connects users to a Dask cluster. It provides an asynchronous user
interface around functions and futures

host
 Hostname of the machine running the scheduler. Defaults to localhost.

port
 Port of the remote scheduler api process. Defaults to 8786.

name
 Gives the client a name that will be included in logs generated on the scheduler for matters relating to this client

timeout
 Timeout duration in seconds for initial connection to the scheduler. Default to 10.

asynchronous
 Set to True if using this client within async/await functions or within Tornado gen.coroutines.  Otherwise this should
 remain False for normal use.Default to False

heartbeat_interval
 Time in milliseconds between heartbeats to scheduler

maxpoolsize
 size of pool client connection

dep_files
 path to dask tasks dependencies zip file

[worker]
--------

These parameters control the Worker (When launching function via Client instance Not when create a cluster).

memory
 Memory to allocate in worker to perform some calculation. Default all available memory

cpu
 number of cpu to allocate in worker to perform some calculation. Default all available cpu
