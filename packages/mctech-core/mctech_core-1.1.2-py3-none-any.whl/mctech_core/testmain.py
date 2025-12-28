from __future__ import absolute_import
import unittest
from os import path, environ
environ['NODE_CONFIG_DIR'] = path.join(path.dirname(__file__), "tests")

__dir__ = path.dirname(__file__)
discover = unittest.defaultTestLoader.discover(path.join(__dir__, "tests"), pattern="*_test.py")
runner = unittest.TextTestRunner()
runner.run(discover)
