import os
from configparser import NoSectionError, NoOptionError
from unittest import TestCase


class ConfigTest(TestCase):

    def tearDown(self) -> None:
        if os.environ.get('DASK_UTILS_ROOT_CONFIG') is not None:
            del os.environ["DASK_UTILS_ROOT_CONFIG"]

    def setUp(self) -> None:

        if os.environ.get('DASK_UTILS_ROOT_CONFIG') is not None:
            del os.environ["DASK_UTILS_ROOT_CONFIG"]

    def test_load_config_default_behavior(self):
        with self.assertRaises(FileNotFoundError):
            from dask_utils import config
            config.get_config()

    def test_load_config_with_env_var_1(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "file_not_exist.cfg"
        with self.assertRaises(FileNotFoundError):
            from dask_utils import config
            config.get_config()

    def test_load_config_with_env_var_2(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb.cfg"
        from dask_utils import config
        self.assertEqual(config.get_config().get('section1', "f1"), 'v1')

    def test_sections_and_options(self):
        os.environ['DASK_UTILS_ROOT_CONFIG'] = "tests/data/mlb.cfg"
        from dask_utils import config
        self.assertEqual(config.get_config().get('section1', "f1"), 'v1')
        with self.assertRaises(NoSectionError):
            config.get_config().get('section', "f1")
        with self.assertRaises(NoOptionError):
            config.get_config().get('section1', "t1")

        self.assertEqual(config.get_config().get('section1', "t1", fallback='default_t1'), 'default_t1')
