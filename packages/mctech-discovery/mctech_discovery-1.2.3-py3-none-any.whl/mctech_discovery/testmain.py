from __future__ import absolute_import
import unittest
from os import path, environ
environ['NODE_CONFIG_DIR'] = path.join(path.dirname(__file__), "tests")


def _init_discovery():
    from mctech_discovery.discovery import get_discovery
    discovery = get_discovery()
    discovery.start()
    configure = discovery.load_config()
    discovery.register()
    configure.merge()


_init_discovery()
__dir__ = path.dirname(__file__)
discover = unittest.defaultTestLoader.discover(path.join(__dir__, "tests"), pattern="*_test.py")
runner = unittest.TextTestRunner()
runner.run(discover)
