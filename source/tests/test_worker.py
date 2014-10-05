__author__ = 'Mike'
import unittest
import mock
from source.lib import worker

class WorkerTestCase(unittest.TestCase):
    def setUp(self):
        self.config = mock.MagicMock()
        self.input_tube = mock.MagicMock()
        self.output_tube = mock.MagicMock()
        worker.logger = mock.MagicMock()