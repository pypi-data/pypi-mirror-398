import os
from unittest import TestCase
import shutil

ROOT = 'tests'
TEMP_DIR = 'target'
ZIP_NAME = 'target.zip'


class ConfigTest(TestCase):

    @classmethod
    def tearDownClass(cls) -> None:
        for f in os.listdir(ROOT):
            if f in (TEMP_DIR, ZIP_NAME):
                path = os.path.join(ROOT, f)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        if os.environ.get('DASK_UTILS_ROOT_CONFIG') is not None:
            del os.environ["DASK_UTILS_ROOT_CONFIG"]

    @classmethod
    def setUpClass(cls) -> None:
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb_with_client.cfg"

    def test_copy_dependencies(self):
        from dask_utils import packaging
        packaging.copy_dependencies(ROOT, os.path.join(ROOT, TEMP_DIR))
        self.assertEqual(os.path.exists(os.path.join(ROOT, TEMP_DIR)), True)

    def test_package_dependencies(self):
        from dask_utils import packaging
        packaging.package_dependencies(os.path.join(ROOT, TEMP_DIR), os.path.join(ROOT, ZIP_NAME))
        self.assertEqual(os.path.exists(os.path.join(ROOT, ZIP_NAME)), True)
