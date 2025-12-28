import os
import time
import unittest

from distributed import LocalCluster

def increment(x):
    return x + 1

class QueueDaskTest(unittest.TestCase):

    def test_01_put_item(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        from dask_utils.config import get_dask_queue
        from dask_utils.queue import Item

        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(name='midnight', project_id=1)
            fut_1 = c.submit(increment, 10)
            queue = get_dask_queue()
            queue.put(Item(1, c, fut_1))
            self.assertEqual(queue.size(), 1)
            c.close()

    def test_get_item(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        from dask_utils.config import get_dask_queue
        from dask_utils.queue import Item

        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(name='midnight', project_id=1)
            fut_1 = c.submit(increment, 10)
            queue = get_dask_queue()
            queue.put(Item(1, c, fut_1))
            actual_key = queue.q[1].future.key
            expected_key = fut_1.key
            self.assertEqual(actual_key, expected_key)

            actual_item = queue.get_item_by_(1)
            self.assertEqual(actual_item.future.key, actual_key)
            self.assertEqual(actual_item.project_id, 1)
            self.assertEqual(actual_item.client, c)
            c.close()

    def test_02_failed(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        from dask_utils.config import get_dask_queue
        from dask_utils.queue import Item, QueueError
        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(name='midnight')
            fut_1 = c.submit(increment, 10)
            queue = get_dask_queue()
            queue.put(Item(client=c, future=fut_1))
            self.assertRegex(fut_1.key, "increment-midnight-prj_None-(\d+)")

            queue = get_dask_queue()
            with self.assertRaisesRegex(QueueError, "The project_id = 2 is not found in queue"):
                queue.get_item_by_(2)
            c.close()
    def test_get_result_by_project_id(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        from dask_utils.config import get_dask_queue
        from dask_utils.queue import Item, QueueError
        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(name='midnight', project_id=1)
            fut_1 = c.submit(increment, 10)
            queue = get_dask_queue()
            queue.put(Item(project_id=1, client=c, future=fut_1))
            self.assertRegex(fut_1.key, "increment-midnight-prj_1-(\d+)")
            time.sleep(3)  # time needed to compute
            queue = get_dask_queue()
            actual_result = queue.get_result_by_project_id(1)
            expected_result = 11
            self.assertEqual(actual_result, expected_result)
            with self.assertRaisesRegex(QueueError, "The project_id = 1 is not found in queue"):
                queue.get_item_by_(1)
            c.close()

    def test_get_dask_queue(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb.cfg"
        from dask_utils.config import get_dask_queue
        from dask_utils.queue import DaskQueue
        from dask_utils.queue import Item
        from distributed import Client

        inst_1 = get_dask_queue()
        inst_1.put(Item(client=Client()))
        self.assertIsInstance(inst_1, DaskQueue)
        inst_2 = get_dask_queue()
        self.assertEqual(inst_1, inst_2)  # test singleton

    def test_cancel_and_remove(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        from dask_utils.config import get_dask_queue
        from dask_utils.queue import Item, QueueError
        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(name='midnight', project_id=1)
            fut_1 = c.submit(increment, 10)
            queue = get_dask_queue()
            queue.put(Item(project_id=1, client=c, future=fut_1))
            time.sleep(3)  # time needed to compute
            actual = queue.cancel_and_remove(1)
            self.assertTrue(actual)
            with self.assertRaisesRegex(QueueError, "The project_id = 1 is not found in queue"):
                queue.cancel_and_remove(1)
            with self.assertRaisesRegex(QueueError, "The project_id = 1 is not found in queue"):
                queue.get_item_by_(1)
            c.close()

    def test_item_repr_and_eq(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        from dask_utils.queue import Item
        from distributed import LocalCluster

        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(name='midnight', project_id=1)
            fut = c.submit(increment, 1)

            item1 = Item(1, c, fut)
            item2 = Item(1, c, fut)

            self.assertEqual(item1, item2)
            self.assertIn("Item", repr(item1))
            c.close()

    def test_put_wrong_type(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        from dask_utils.config import get_dask_queue
        from dask_utils.queue import QueueError

        queue = get_dask_queue()
        with self.assertRaises(QueueError):
            queue.put("not-an-item")

    def test_get_item_invalid_status(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        from dask_utils.queue import Item, QueueError
        from dask_utils.config import get_dask_queue
        from distributed import LocalCluster

        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(name='midnight', project_id=1)
            fut = c.submit(increment, 1)
            queue = get_dask_queue()
            queue.put(Item(1, c, fut))

            with self.assertRaises(QueueError):
                queue.get_item_by_(1, status="UNKNOWN")
            c.close()
