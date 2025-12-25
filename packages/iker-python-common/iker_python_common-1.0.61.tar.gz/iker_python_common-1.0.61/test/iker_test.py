import unittest

from iker_tests import *


class Test(unittest.TestCase):

    def test(self):
        self.assertIsNotNone(module_directory)
        self.assertIsNotNone(source_directory)
        self.assertIsNotNone(test_directory)
        self.assertIsNotNone(resources_directory)
        self.assertIsNotNone(temporary_directory)
