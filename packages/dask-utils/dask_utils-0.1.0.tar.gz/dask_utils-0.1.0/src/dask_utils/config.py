import logging
import os
import configparser
import errno

logger = logging.getLogger('dask_utils')

PARSERS = {
    'cfg': configparser.ConfigParser,
}
""" parser class used when read config file, ypu can add you custom parser here (e.g YAML parser) """

DEFAULT_PARSER = 'cfg'
""" default parser class"""

DEFAULT_ROOT_CONFIG = 'config/client.cfg'
""" default DASK_UTILS_ROOT_CONFIG file path, used if env var `DASK_UTILS_ROOT_CONFIG` is not defined"""


def path_exp_to_resource_path():
    """
    Retrieve the env var `DASK_UTILS_ROOT_CONFIG`
    if not exist, return the default value `DEFAULT_ROOT_CONFIG`
    :return path to config file
    """
    return os.environ.get('DASK_UTILS_ROOT_CONFIG', DEFAULT_ROOT_CONFIG)


def get_config(path=None):
    """ Check the conf file given in path and return the parser object.

     This method check existing of a resource pointed by a given path expression and
     raises an exception if it does not not exist.

     :arg path: path expression pointing a resource in a module
     :return object: the parser instance (`ConfigParser` by default)
     :raises FileNotFoundError: if the resource pointed by the path doe not exist

     """
    if not path:
        path = path_exp_to_resource_path()

    if not os.path.exists(path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

    _inst = PARSERS[DEFAULT_PARSER]()
    _inst.read(filenames=path)
    return _inst


def get_dask_queue():
    """Get Queue Singleton instance
    """
    from dask_utils.queue import DaskQueue
    clazz = DaskQueue
    return clazz.instance()
