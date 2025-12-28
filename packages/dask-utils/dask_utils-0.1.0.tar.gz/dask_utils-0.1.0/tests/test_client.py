import os
import unittest

os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"


def increment(x):
    return x + 1

from distributed.client import Future


class ClientTest(unittest.TestCase):

    # TODO: SKIPPED for this release : we can not add worker resources when use LocalCLuster: to see another alternative
    #     y = c.submit(inc, 20, resources={'memory': 11e9, 'cpu': 3, 'process': 1})
    # we need to add to file
    # [worker]
    # memory=1e5
    # cpu=2
    # process=1

    def test_init_client(self):
        from distributed import LocalCluster
        import dask_utils.client as client

        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(address=cluster.scheduler_address)
            import dask_utils.config as configuration
            host = configuration.get_config().get('client', 'host')
            port = configuration.get_config().getint('client', 'port')
            as_dict = c.__dict__
            self.assertEqual(as_dict['address'], 'tcp://{}:{}'.format(host, port))
            c.close()
    def test_submit(self):

        from distributed import LocalCluster
        import dask_utils.client as client

        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(address=cluster.scheduler_address)
            f = c.submit(increment, 10)
            self.assertIsInstance(f, Future)
            self.assertEqual(f.client, c)
            self.assertEqual(f.done(), False)
            self.assertEqual(f.result(timeout=5), 11)
            self.assertEqual(f.done(), True)
            c.close()

    def test_map(self):
        from distributed import LocalCluster
        import dask_utils.client as client

        with LocalCluster(scheduler_port=51009, n_workers=1) as cluster:
            c = client.DaskClient(address=cluster.scheduler_address)
            x_m = c.map(increment, range(10))

            for fut in x_m:
                self.assertEqual(fut.done(), False)
                self.assertIsInstance(fut, Future)
                self.assertEqual(fut.client, c)

            for i, fut in enumerate(x_m):
                result = fut.result(timeout=5)
                self.assertEqual(result, i + 1)
                self.assertEqual(fut.done(), True)
            c.close()

    def test_compute(self):

        from distributed import LocalCluster
        import dask_utils.client as client
        from dask import delayed
        from operator import add

        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(address=cluster.scheduler_address)
            x = delayed(add)(1, 2)
            y = delayed(add)(x, x)
            xx, yy = c.compute([x, y])

            result_xx = xx.result()
            self.assertEqual(result_xx, 3)
            result_yy = yy.result()
            self.assertEqual(result_yy, 6)
            c.close()
    def test_submit_map_keys(self):

        import dask_utils.client as client

        from distributed import LocalCluster
        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            c = client.DaskClient(name='midnight', project_id=1)
            f = c.submit(increment, 10)
            f1 = c.map(increment, [10, 10])
            import re
            re1 = '((?:[a-z][a-z]+))'
            re2 = '(-)'
            re3 = '(midnight)'
            re4 = '.*?'
            re5 = '(prj_1)'
            re6 = '([-+]\\d+)'

            rg = re.compile(re1 + re2 + re3 + re4 + re5 + re6)
            self.assertTrue(rg.search(f.key))
            for fut in f1:
                self.assertTrue(rg.search(fut.key))
            c.close()
    def test_gets_status(self):

        import dask_utils.client as client

        from distributed import LocalCluster
        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            import time

            c = client.DaskClient(name='midnight', project_id=1)
            fut_1 = c.submit(increment, 10)
            fut_2 = c.submit(increment, 20)
            st_1 = c.get_task_status_by_key(fut_1.key)
            st_2 = c.get_task_status_by_key(fut_2.key)
            self.assertEqual(st_1, 'pending')
            self.assertEqual(st_2, 'pending')
            res1 = c.gather(fut_1)
            time.sleep(3)
            st_1 = c.get_task_status_by_key(fut_1.key)
            self.assertEqual(st_1, 'finished')
            self.assertEqual(st_2, 'pending')
            res2 = c.gather(fut_2)
            time.sleep(3)
            st_2 = c.get_task_status_by_key(fut_2.key)
            self.assertEqual(st_2, 'finished')
            with self.assertRaises(client.TaskNotFoundError):
                c.get_task_status_by_key(121212)  # task key not exist
            c.close()
    def test_kill(self):

        import dask_utils.client as client

        from distributed import LocalCluster
        with LocalCluster(scheduler_port=51009, n_workers=2) as cluster:
            import time

            c = client.DaskClient(name='midnight', project_id=1)
            fut_1 = c.submit(increment, 10)
            st_1 = c.get_task_status_by_key(fut_1.key)
            self.assertNotEqual(st_1, 'cancelled')
            c.kill_tasks([fut_1])
            time.sleep(2)
            self.assertEqual(fut_1.status, 'cancelled')
            with self.assertRaises(client.TaskNotFoundError):  # ensure that the future are deleted from client
                c.get_task_status_by_key(fut_1.key)
            c.close()