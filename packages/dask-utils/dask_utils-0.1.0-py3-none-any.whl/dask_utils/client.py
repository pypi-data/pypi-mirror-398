"""
 Module implements a custom client dask

"""
from typing import Any

from dask.distributed import Client

import dask_utils.config as configuration
from dask_utils.decorators import Singleton

import logging
logger = logging.getLogger(__name__)


class DaskComputeError(Exception):
    """Dask compute Error.

    Attributes:
        details: detailed information about the error
    """

    def __init__(self, **details):
        super(DaskComputeError, self).__init__(details)
        self.details = details


class TaskNotFoundError(Exception):
    """Task Not Found Error.

    Attributes:
        details: detailed information about the error
    """

    def __init__(self, **details):
        super(TaskNotFoundError, self).__init__(details)
        self.details = details


DEFAULT_RESOURCES_OPTIONS = ['cpu', 'gpu', 'memory', 'process']
""" List of configuration taken in consideration """

DEFAULT_EXTENSIONS: dict[str, Any] = {}
""" Extend Dask's Client with handlers to handle PubSub machinery """


@Singleton(enable=False)
class DaskClient(Client):
    """Custom patch which allows create a dask `Client` with custom parameters defined in `client.cfg` config file.
    Connect and submit computation on  Dask cluster

    Examples::
    --------
    >>> from dask_utils import Client
    >>> Client().submit(f,arg)


    Attributes
    address: string, or Cluster
        This can be the address of a ``Scheduler`` server like a string
        ``'127.0.0.1:8786'`` or a cluster object like ``LocalCluster()``
    timeout: int
        Timeout duration for initial connection to the scheduler
    set_as_default: bool (True)
        Claim this scheduler as the global dask scheduler
    scheduler_file: string (optional)
        Path to a file with scheduler information if available
    security: (optional)
        Optional security information
    asynchronous: bool (False by default)
        Set to True if using this client within async/await functions or within
        Tornado gen.coroutines.  Otherwise this should remain False for normal
        use.
    name: string (optional)
        Gives the client a name that will be included in logs generated on
        the scheduler for matters relating to this client
    direct_to_workers: bool (optional)
        Whether or not to connect directly to the workers, or to ask
        the scheduler to serve as intermediary.
    heartbeat_interval: int
        Time in milliseconds between heartbeats to scheduler
    **kwargs:
        If you do not pass a scheduler address, Client will create a
        ``LocalCluster`` object, passing any extra keyword arguments.

    """

    @property
    def _client_section_name(self):
        return "client"

    @property
    def _worker_section_name(self):
        return "worker"

    @property
    def __host(self):
        return configuration.get_config().get(self._client_section_name, 'host', fallback='localhost')

    @property
    def __port(self):
        return configuration.get_config().getint(self._client_section_name, 'port', fallback='8786')

    @property
    def __timeout(self):
        return configuration.get_config().get(self._client_section_name, "timeout", fallback=None)

    @property
    def __asynchronous(self):
        return configuration.get_config().getboolean(self._client_section_name, "asynchronous", fallback=False)

    @property
    def __name(self):
        return configuration.get_config().get(self._client_section_name, "name", fallback=None)

    @property
    def __heartbeat_interval(self):
        return configuration.get_config().getint(self._client_section_name, "heartbeat_interval", fallback=None)

    @property
    def __direct_to_workers(self):
        return configuration.get_config().getboolean(self._client_section_name, "direct_to_workers", fallback=False)

    @property
    def __security(self):
        return configuration.get_config().get(self._client_section_name, "security", fallback=None)

    @property
    def __set_as_default(self):
        return configuration.get_config().getboolean(self._client_section_name, "set_as_default", fallback=True)

    @property
    def __dep_files(self):
        return configuration.get_config().get(self._client_section_name, "dep_files", fallback=None)

    @property
    def __cpu(self):
        return configuration.get_config().getint(self._worker_section_name, "cpu", fallback=None)

    @property
    def __gpu(self):
        return configuration.get_config().get(self._worker_section_name, "gpu", fallback=None)

    @property
    def __memory(self):
        return configuration.get_config().getfloat(self._worker_section_name, "memory", fallback=None)

    @property
    def __process(self):
        return configuration.get_config().getint(self._worker_section_name, "process", fallback=None)

    def _key(self, f):
        from datetime import datetime
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        return '{}-{}-{}'.format(f.__name__, self.name, ts)

    def __init__(self,
                 address=None,
                 loop=None,
                 timeout=None,
                 set_as_default=True,
                 scheduler_file=None,
                 security=None,
                 asynchronous=False,
                 name=None,
                 project_id=None,
                 heartbeat_interval=None,
                 serializers=None,
                 deserializers=None,
                 extensions=DEFAULT_EXTENSIONS,
                 direct_to_workers=None,
                 **kwargs
                 ):
        self.address = address or '{}:{}'.format(self.__host, self.__port)
        self.cpu = self.__cpu
        self.gpu = self.__gpu
        self.memory = self.__memory
        self.process = self.__process
        self.timeout = timeout or self.__timeout
        self.set_as_default = set_as_default or self.__set_as_default
        self.security = security or self.__security
        self.asynchronous_ = asynchronous or self.__asynchronous
        self.name = (name or self.__name) + '-prj_' + str(project_id)
        # self.name = name or self.__name
        self.heartbeat_interval = heartbeat_interval or self.__heartbeat_interval
        self.direct_to_workers = direct_to_workers or self.__direct_to_workers
        self._resources = dict((k, self.__dict__[k]) for k in DEFAULT_RESOURCES_OPTIONS
                               if k in self.__dict__ and self.__dict__[k] is not None)

        super().__init__(
            address=self.address,
            timeout=self.timeout,
            set_as_default=self.set_as_default,
            security=self.security,
            asynchronous=self.asynchronous_,
            loop=loop,
            name=self.name,
            heartbeat_interval=self.heartbeat_interval,
            direct_to_workers=self.direct_to_workers,
            scheduler_file=scheduler_file,
            serializers=serializers,
            deserializers=deserializers,
            extensions=extensions,
            **kwargs
        )
        if self.__dep_files:
            self.upload_file(self.__dep_files)
        self._init_logger_config()

    def _init_logger_config(self):
        def init_logger(logging_config_worker):
            import logging.config
            logging.config.fileConfig(logging_config_worker)

        try:
            logging_config_worker = configuration.get_config().get("client", "logging_config_worker", fallback=None)
            if logging_config_worker:
                logger.info("configure dask worker logger...")
                self.run(init_logger, logging_config_worker)
                logger.info("configure dask worker logger OK")

        except Exception as e:
            logger.exception(e)

    def get_task_status_by_key(self, task_key):
        """
        Search by task key and return the given task status

        If the task exist, then return the status
        else, and opposite  of native implementation if (Future(key,client).status) which return pending if the task does
        not exit, this function raise an exception

        :parameter
        task_key : str
            task id with pattern '<<func>>-<<client_name>>-<<prj_id>>-<<YYYYMMDDHHMMSS>>'

        :return
        status (str)
        :raises
        TaskNotFoundError
        """

        if task_key in self.futures:
            return self.futures[task_key].status
        else:
            raise TaskNotFoundError(
                message='There is no task found on client:{} with key = {}'.format(self.name, task_key)
            )

    def kill_tasks(self, futures, asynchronous=None, force=False):
        """
        Kill running futures

        This stops future tasks from being scheduled if they have not yet run
        and deletes them if they have already run.  After calling, this result
        and all dependent results will no longer be accessible

        :parameter
        futures: list
            list of Futures
        asynchronous : bool
        force: boolean (False)
            Cancel this future even if other clients desire it
        """
        sync = asynchronous or self.asynchronous_
        self.cancel(futures=futures, asynchronous=sync, force=force)

    def submit(self, func, *args, key=None, workers=None, resources=None, retries=None, priority=0,
               fifo_timeout="100 ms", allow_other_workers=False, actor=False, actors=False, pure=None, **kwargs):
        """ Submit a function application to the scheduler

        :parameter
        func: callable
        *args:
        key: str
            Unique identifier for the task.  Defaults to function-name and hash
        workers: set, iterable of sets
            A set of worker hostnames on which computations may be performed.
            Leave empty to default to all workers (common case)
        resources : dict
            A dict of configuration options to send to scheduler
        retries: int (default to 0)
            Number of allowed automatic retries if the task fails
        priority: Number
            Optional prioritization of task.  Zero is default.
            Higher priorities take precedence
        fifo_timeout: str timedelta (default '100ms')
            Allowed amount of time between calls to consider the same priority
        allow_other_workers: bool (defaults to False)
            Used with `workers`. Indicates whether or not the computations
            may be performed on workers that are not in the `workers` set(s).
        pure: bool (defaults to True)
            Whether or not the function is pure.  Set ``pure=False`` for
            impure functions like ``np.random.random``.
        **kwargs:

        Examples
        --------
        >>> c = client.submit(add, a, b)

        :returns
        Future

        See Also
        --------
        DaskClient.map: Submit on many arguments at once
        DaskClient.compute : Compute dask collections on cluster
        """
        return super().submit(func,
                              *args,
                              key=key or self._key(func),
                              workers=workers,
                              resources=(resources or self._resources),
                              retries=retries,
                              priority=priority,
                              fifo_timeout=fifo_timeout,
                              allow_other_workers=allow_other_workers,
                              actor=actor,
                              actors=actors,
                              pure=pure,
                              **kwargs
                              )

    def map(self, func, *iterables, key=None, workers=None, retries=None, resources=None, priority=0,
            allow_other_workers=False, fifo_timeout="100 ms", actor=False, actors=False, pure=None, **kwargs):
        """ Map a function on a sequence of arguments

        Arguments can be normal objects or Futures

        :parameter
        func: callable
        iterables: Iterables
            List-like objects to map over.  They should have the same length.
        key: str, list
            Prefix for task names if string.  Explicit names if list.
        pure: bool (defaults to True)
            Whether or not the function is pure.  Set ``pure=False`` for
            impure functions like ``np.random.random``.
        workers: set, iterable of sets
            A set of worker hostnames on which computations may be performed.
            Leave empty to default to all workers (common case)
        retries: int (default to 0)
            Number of allowed automatic retries if a task fails
        priority: Number
            Optional prioritization of task.  Zero is default.
            Higher priorities take precedence
        fifo_timeout: str timedelta (default '100ms')
            Allowed amount of time between calls to consider the same priority
        **kwargs: dict
            Extra keywords to send to the function.
            Large values will be included explicitly in the task graph.

        Examples
        --------
        >>> L = client.map(func, sequence)  # doctest: +SKIP

        :returns
        List, iterator, or Queue of futures, depending on the type of the
        inputs.

        See also
        --------
        DaskClient.submit: Submit a single function
        DaskClient.compute: Compute dask collections on cluster
        """
        return super().map(func,
                           *iterables,
                           key=key or self._key(func),
                           workers=workers,
                           retries=retries,
                           resources=(resources or self._resources),
                           priority=priority,
                           allow_other_workers=allow_other_workers,
                           fifo_timeout=fifo_timeout,
                           actor=actor,
                           actors=actors,
                           pure=pure,
                           **kwargs)

    def compute(self, collections, sync=False, optimize_graph=True, workers=None, allow_other_workers=False,
                resources=None, retries=0, priority=0, fifo_timeout="60s", actors=None, traverse=True, **kwargs):
        """ Compute dask collections on cluster

        :parameter
        collections: iterable of dask objects or single dask object
            Collections like dask.array or dataframe or dask.value objects
        sync: bool (optional)
            Returns Futures if False (default) or concrete values if True
        optimize_graph: bool
            Whether or not to optimize the underlying graphs
        workers: str, list, dict
            Which workers can run which parts of the computation
            If a string a list then the output collections will run on the listed
            workers, but other sub-computations can run anywhere
            If a dict then keys should be (tuples of) collections and values
            should be addresses or lists.
        allow_other_workers: bool, list
            If True then all restrictions in workers= are considered loose
            If a list then only the keys for the listed collections are loose
        retries: int (default to 0)
            Number of allowed automatic retries if computing a result fails
        priority: Number
            Optional prioritization of task.  Zero is default.
            Higher priorities take precedence
        fifo_timeout: timedelta str (defaults to '60s')
            Allowed amount of time between calls to consider the same priority
        **kwargs:
            Options to pass to the graph optimize calls

        :returns
        List of Futures if input is a sequence, or a single future otherwise

        Examples
        --------
        >>> from dask import delayed
        >>> from operator import add
        >>> x = delayed(add)(1, 2)
        >>> y = delayed(add)(x, x)
        >>> xx, yy = client.compute([x, y])  # doctest: +SKIP
        >>> xx  # doctest: +SKIP
        <Future: status: finished, key: add-8f6e709446674bad78ea8aeecfee188e>
        >>> xx.result()  # doctest: +SKIP
        3
        >>> yy.result()  # doctest: +SKIP
        6

        Also support single arguments

        >>> xx = client.compute(x)  # doctest: +SKIP

        See Also
        --------
        DaskClient.submit: Submit a single function
        DaskClient.map: Submit on many arguments at once
        """
        return super().compute(collections,
                               sync=False,
                               optimize_graph=True,
                               workers=None,
                               allow_other_workers=False,
                               resources=(resources or self._resources),
                               retries=0,
                               priority=0,
                               fifo_timeout="60s",
                               actors=None,
                               traverse=True,
                               **kwargs
                               )
