"""module implements different decorators

 This modules give some useful decorators used by dask-utils

"""
import dask_utils.config as configuration

POOL_SIZE = configuration.get_config().getint('client', "maxpoolsize", fallback=50)
"""Size of connection pool"""


class Singleton:
    """
     A decorate singleton class used to provide one and only one object of ``dask_utils.client.DaskClient``


     Two instances of ``dask_utils.client.DaskClient`` are considered equal if :

     * they have the same ``name`` , and
     * they have the same ``project_id``

     The Clients recently instantiated are cached into a pool, every time when you need to create a new client connection
     the Singleton class search into this pool an existing client, if exist, it will be returned, else, if the maximum number
     of connection pool is not reached, a new Client will be created and added to pool as new element.

     The size of the connection pool is configurable into config file, [client] section::

        [client]
        maxpoolsize=10

     The default size number is set to 50

     Set ``maxpoolsize=0``, to get an unlimited pool

     You need to provide a connection pool size at the time of its creation. You cannot change the size once created.

     By default, the singleton is enabled, you can disabled it by passing `enable` to False:


     Examples::

     >>> ...                             # doctest: +SKIP
     >>> @Singleton(enable=False)        # doctest: +SKIP
     >>> class DaskClient(Client):   # doctest: +SKIP
     >>> ...                             # doctest: +SKIP

     Or

     >>> ...
     >>> @Singleton(enable=True)        # doctest: +SKIP
     >>> class DaskClient(Client):  # doctest: +SKIP
     >>> ...                            # doctest: +SKIP

     :param
     ----------
     enable: bool
            If True, the Singleton will be executed

     :return
     ----------
     object: DASKClient
        a Client instance

     :raise
     ----------
     IndexError:
        If maximum number of connection pool is reached
     """

    def __init__(self, enable=True):
        self.enable = enable

    def __call__(self, cls):
        _pool = dict()

        def _(*args, **kwargs):
            if 'name' in kwargs:
                _name = kwargs['name']
            else:
                _name = configuration.get_config().get('client', "name", fallback=None)

            if 'project_id' in kwargs:
                _id = kwargs['project_id']
            else:
                self.enable = False  # we disable singleton in this case
                _id = None

            if self.enable:
                if not _pool:
                    instance = cls(*args, **kwargs)
                    _pool[(_name, _id)] = instance
                elif (_name, _id) in _pool:
                    instance = _pool[(_name, _id)]
                else:
                    if len(_pool) < POOL_SIZE:
                        instance = cls(*args, **kwargs)
                        _pool[(_name, _id)] = instance
                    else:
                        raise IndexError('The maximum connections supported by the server is reached')
                return instance
            else:
                return cls(*args, **kwargs)

        return _
