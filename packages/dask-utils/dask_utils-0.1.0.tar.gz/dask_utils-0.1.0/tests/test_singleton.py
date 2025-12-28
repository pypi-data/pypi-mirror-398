import os
import unittest

import pytest
from distributed import LocalCluster
from tornado.ioloop import IOLoop

loop = IOLoop.current()


class SingletonTest(unittest.TestCase):

    @pytest.mark.skip(reason="Singleton is disabled in DaskClient for this version")
    def test_singleton(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        import importlib
        importlib.reload(client)  # reload is used to initialize _pool
        with LocalCluster(scheduler_port=51009) as cluster:
            c_n1_p1 = client.DaskClient(address=cluster.scheduler_address, name='n1', project_id=1)
            c_n2_p1 = client.DaskClient(address=cluster.scheduler_address, name='n2', project_id=1)
            c_n1_p2 = client.DaskClient(address=cluster.scheduler_address, name='n1', project_id=2)
            c_n1_p1_ = client.DaskClient(address=cluster.scheduler_address, name='n1', project_id=1)
            c_n_default_p1 = client.DaskClient(address=cluster.scheduler_address, project_id=1)
            c_n_default_p1_ = client.DaskClient(address=cluster.scheduler_address, name='test_client', project_id=1)
            c_n_default_port_default_p1 = client.DaskClient(project_id=1)

            self.assertNotEqual(c_n1_p1, c_n2_p1)
            self.assertNotEqual(c_n1_p1, c_n1_p2)
            self.assertEqual(c_n1_p1, c_n1_p1_)
            self.assertNotEqual(c_n1_p1, c_n_default_p1)
            self.assertNotEqual(c_n1_p1, c_n_default_p1_)
            self.assertNotEqual(c_n1_p1, c_n_default_port_default_p1)

            self.assertNotEqual(c_n2_p1, c_n1_p2)
            self.assertNotEqual(c_n2_p1, c_n1_p1_)
            self.assertNotEqual(c_n2_p1, c_n_default_p1)
            self.assertNotEqual(c_n2_p1, c_n_default_p1_)
            self.assertNotEqual(c_n2_p1, c_n_default_port_default_p1)

            self.assertNotEqual(c_n1_p2, c_n1_p1_)
            self.assertNotEqual(c_n1_p2, c_n_default_p1)
            self.assertNotEqual(c_n1_p2, c_n_default_p1_)
            self.assertNotEqual(c_n1_p2, c_n_default_port_default_p1)

            self.assertNotEqual(c_n1_p1_, c_n_default_p1)
            self.assertNotEqual(c_n1_p1_, c_n_default_p1_)
            self.assertNotEqual(c_n1_p1_, c_n_default_port_default_p1)

            self.assertEqual(c_n_default_p1, c_n_default_p1_)
            self.assertEqual(c_n_default_p1, c_n_default_port_default_p1)

    @pytest.mark.skip(reason="Singleton is disabled in DaskClient for this version")
    def test_pool_connection(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"
        import dask_utils.client as client
        import importlib
        importlib.reload(client)  # reload is used to initialize _pool
        with LocalCluster(scheduler_port=51009, loop=IOLoop.instance()) as cluster:
            for i in range(10):  # maxpoolsize=10
                c_ok = client.DaskClient(address=cluster.scheduler_address, name='n' + str(i), project_id=1)
            with self.assertRaises(IndexError):
                c_ko = client.DaskClient(address=cluster.scheduler_address, name='n', project_id=1)  # 11th instance
