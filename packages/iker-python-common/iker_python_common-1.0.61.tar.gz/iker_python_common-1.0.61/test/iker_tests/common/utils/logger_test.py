import unittest

from iker.common.utils import logger


class LoggerTest(unittest.TestCase):

    def test_debug(self):
        self.assertEqual(__name__, logger.debug("This is a log"))

    def test_info(self):
        self.assertEqual(__name__, logger.info("This is a log"))

    def test_warning(self):
        self.assertEqual(__name__, logger.warning("This is a log"))

    def test_error(self):
        self.assertEqual(__name__, logger.error("This is a log"))

    def test_critical(self):
        self.assertEqual(__name__, logger.critical("This is a log"))
