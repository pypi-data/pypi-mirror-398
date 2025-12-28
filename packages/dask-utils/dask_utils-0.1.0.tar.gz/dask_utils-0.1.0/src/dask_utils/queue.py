"""
This module offers the possibility to save, track and retrieve Dask computation results

"""
import logging

from distributed import Client

from dask_utils.client import DaskComputeError

logger = logging.getLogger(__name__)
QUEUE_SIZE = 50
"""Size of Queue"""

PENDING = "pending"
FINISHED = "finished"
CLOSED = "closed"
CLOSING = "closing"
CREATED = "newly-created"
CONNECTING = "connecting"
RUNNING = "running"
__not_mentioned__ = '__not_mentioned__'

DEFAULT_STATUS = __not_mentioned__
STATUS = [
    PENDING,
    FINISHED,
    CLOSED,
    CREATED,
    CONNECTING,
    RUNNING,
    __not_mentioned__
]


class QueueError(Exception):
    """QueueError Error.

    :param details: detailed information about the error
    """

    def __init__(self, **details):
        super(QueueError, self).__init__(details)
        self.details = details


class Item:
    """Item element.
    A wrapper object to define the item information.

    :param project_id: project id, id of Future in Queue
    :param client: Dask Client.
    :param future: Dask Future
    :param key: Custom key to identify Dask Future
    :param *args: args
    :param **kwargs: kwargs.
    """

    def __init__(self, project_id=None, client=None, future=None, key=None, *args, **kwargs):

        if not isinstance(client, Client):
            raise QueueError(
                message='Client parameter is not an instance of DaskClient.')

        if not project_id:
            import warnings

            warning_message = '''
            <<project_id>> is not mentioned, this may cause a potential problem when trying to retrieve element
            from the queue
                '''
            warnings.warn(warning_message, )

        self.project_id = project_id
        self.client = client
        self.future = future
        self.key = key
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

    def __eq__(self, o):
        return self.__dict__ == o.__dict__ if isinstance(o, Item) else False


class DaskQueue:
    """ A queue utility in which producer (e.g Helperv2) and consumer (e.g external API) can write, read and track
    Dask computation on cluster.

    This class doesn't inherit Queue class distributed package for the simple reason, the futures in DaskQueue are
    issue from multiple client, it's not the same case with Queue class distributed.

    By default, only one instance (singleton) is available for put/get

    Only one item with the same project_id is allowed to be in the Queue, independently of status of computation

    In this version, we allow putting only one item with project_id equal to None.

    Additionally, The max size of Queue is QUEUE_SIZE = 50

    if user call function get_result_by_project_id, DaskQueue return result and delete item from Queue and delete
    cache from Dask cluster

    :param args: args
    :param kwargs: kwargs.
    """
    _instance = None

    def __init__(self, *args, **kwargs):
        self.q = dict()
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

    @classmethod
    def instance(cls, *args, **kwargs):
        """ Singleton getter """
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)

        return cls._instance

    def put(self, item):
        """Put item into the queue.
        :param item: item to put
        :raise: IndexError if queue max size is reached
         """

        if not isinstance(item, Item):
            raise QueueError(
                message='item parameter is not an instance of Item.')

        if len(self.q) < QUEUE_SIZE:
            self.q[item.project_id] = item
        else:
            raise IndexError('The maximum items supported is reached')

    def get_item_by_(self, project_id, status=None):
        """Remove and return an item from the queue.
        :param project_id: project id
        :param status: Future status
        :return item or None
        :raise: KeyError if project id if not found
        :raise: AttributeError if error in item present in queue
        :raise: Exception if Any other exception occurs
         """
        _status = status or DEFAULT_STATUS
        try:
            if _status not in STATUS:
                raise QueueError(
                    message='{} is unknown status.'.format(_status))

            _item = self.q[project_id]
            _future = _item.future.key
            _client = _item.client

            if _status != __not_mentioned__ and _client.get_task_status_by_key(_future.key) != _status:
                return None
            else:
                return _item
        except KeyError:
            raise QueueError(
                message='The project_id = {} is not found in queue'.format(project_id))
        except AttributeError as e:
            raise QueueError(
                message='Their is a missing attribute in item: {}'.format(e))
        except Exception as e:
            raise QueueError(
                message='An exception occurs when trying to retrieve item: {}'.format(e))

    def get_result_by_project_id(self, project_id):
        """Remove item from queue and return result from Dask.
        Also, deletes data even if other futures point to it (garbage collector dask)

        :param project_id: project id
        :return computation Future result or None if computation not yet completed
        :raise: KeyError if project id if not found
        :raise: AttributeError if error in item present in queue
        :raise: Exception if Any other exception occurs
         """
        _future = None
        try:
            _item = self.q[project_id]
        except KeyError:
            raise QueueError(
                message='The project_id = {} is not found in queue'.format(project_id))
        try:
            _future = _item.future
            _client = _item.client

            if _future.done():
                res = _client.gather(_future)
                del self.q[project_id]
                _future.cancel()
                if _get_workers_status(_client):
                    _client.restart()
                return res
            else:
                return None
        except KeyError as e:
            logger.exception(e)
            raise QueueError(
                message='Their is an error happens in dask calculation project_id={}'.format(project_id))
        except AttributeError as e:
            logger.exception(e)
            raise QueueError(
                message='Their is a missing attribute in item: {}'.format(e))
        except DaskComputeError as e:
            logger.exception(e)
            if _get_workers_status(_client):
                _client.restart()
            raise QueueError(
                message='Their is a missing attribute in item: {}'.format(e))
        except Exception as e:
            logger.exception(e)
            raise QueueError(
                message='An exception occurs when trying to retrieve result: {}'.format(e))
        finally:
            if _future is not None:
                _future.cancel()

    def done(self, project_id):
        """Return True if Future is done, otherwise False

        :param project_id: project id
        :return True if done otherwise False
        :raise: KeyError if project id if not found
        :raise: AttributeError if error in item present in queue
        :raise: Exception if Any other exception occurs
         """
        try:
            _item = self.q[project_id]
            _future = _item.future
            _client = _item.client

            return _future.done()
        except KeyError:
            raise QueueError(
                message='The project_id = {} is not found in queue'.format(project_id))
        except AttributeError as e:
            raise QueueError(
                message='Their is a missing attribute in item: {}'.format(e))
        except Exception as e:
            logger.exception(e)
            raise QueueError(
                message='An exception occurs when trying to retrieve result: {}'.format(e))

    def size(self):
        """Return the size of the queue.

        :return queue size
         """
        return len(self.q)

    def empty(self):
        """Return True if the queue is empty, False otherwise.
        :return True if Queue is empty , otherwise False
         """
        return len(self.q) == 0

    def cancel_and_remove(self, project_id):
        """Cancel actual future and remove item from queue.

        :param project_id: project id
        :return True if success, else raise exception
         """
        try:
            _item = self.q[project_id]
            _future = _item.future
            _item.client.kill_tasks(_future)
            del _future
            del self.q[project_id]
            if _get_workers_status(_item.client):
                _item.client.restart()
            return True
        except KeyError:
            raise QueueError(
                message='The project_id = {} is not found in queue'.format(project_id))
        except AttributeError as e:
            raise QueueError(
                message='Their is a missing attribute in item: {}'.format(e))
        except Exception as e:
            raise QueueError(
                message='An exception occurs when trying to remove and kill future: {}'.format(e))


def _get_workers_status(client):
    infos = client.scheduler_info()
    for k, v in infos['workers'].items():
        logger.info("info for worker: {}".format(k))
        for e, x in v['metrics'].items():
            if e == 'executing':
                if x != 0:
                    logger.info("Their is {} tasks in progress on worker {}. SKIP RESTART WORKER".format(x, k))
                    return False
                else:
                    logger.info("Their is no tasks in progress on worker {}. OK FOR RESTARTING WORKER".format(k))
                    return True
    return None
