__author__ = 'Mike'
import unittest
import mock
from source.lib import worker
from tarantool.error import DatabaseError


class WorkerTestCase(unittest.TestCase):
    def setUp(self):
        self.config = mock.MagicMock()
        self.input_tube = mock.MagicMock()
        self.output_tube = mock.MagicMock()
        worker.logger = mock.MagicMock()

    def test_worker_without_task(self):
        pid = 0
        self.input_tube.take.return_value = None
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[self.input_tube, self.output_tube])):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock()) as history:
                    worker.worker(self.config, pid)
        assert not history.called

    def test_worker_with_empty_result(self):
        pid = 0
        task = mock.Mock()
        self.input_tube.take.return_value = task
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[self.input_tube, self.output_tube])):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=None)):
                    worker.worker(self.config, pid)
        assert task.ack.called

    def test_worker_with_good_result_and_input(self):
        data = (True, "sAAaa")
        pid = 0
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[self.input_tube, self.output_tube])):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=data)):
                    worker.worker(self.config, pid)
        assert self.input_tube.put.called

    def test_worker_with_good_result_and_no_input(self):
        data = (False, "sAAaa")
        pid = 0
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[self.input_tube, self.output_tube])):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=data)):
                    worker.worker(self.config, pid)
        assert self.output_tube.put.called

    def test_worker_with_take_ask_raise(self):
        data = (False, "sAAaa")
        pid = 0
        task = mock.Mock()
        task.ack = mock.Mock(side_effect=DatabaseError)
        self.input_tube.take.return_value = task
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[self.input_tube, self.output_tube])):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=data)):
                    worker.worker(self.config, pid)
        assert worker.logger.exception.called

    def test_get_redirect_history_from_task_with_error_in_history_types(self):
        url = 'http://get.my/com'
        task = mock.Mock()
        is_input = True
        task.data = {
            'url': url,
            'recheck': False,
            'url_id': 0
        }
        with mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value=url)):
            with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=[['ERROR'], [], []])):
                self.assertEqual(worker.get_redirect_history_from_task(task, 10), (is_input, task.data))

    def test_get_redirect_history_from_task_without_error_in_history_types(self):
        url = 'http://get.my/com'
        task = mock.Mock()
        is_input = False
        task.data = {
            'url': url,
            'recheck': False,
            'url_id': 0
        }
        return_for_redirect_history = [['abc'], ['cde'], [123]]
        output = {
            'url_id': task.data['url_id'],
            'result': return_for_redirect_history,
            'check_type': 'normal'
        }
        with mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value=url)):
            with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=return_for_redirect_history)):
                self.assertEqual(worker.get_redirect_history_from_task(task, 10), (is_input, output))

    def test_get_redirect_history_from_task_without_error_in_history_types_and_suspicious(self):
        url = 'http://get.my/com'
        task = mock.Mock()
        is_input = False
        task.data = {
            'url': url,
            'recheck': False,
            'url_id': 0,
            'suspicious': 'FD'
        }
        return_for_redirect_history = [['abc'], ['cde'], [123]]
        output = {
            'url_id': task.data['url_id'],
            'result': return_for_redirect_history,
            'check_type': 'normal',
            'suspicious': task.data['suspicious']
        }
        with mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value=url)):
            with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=return_for_redirect_history)):
                self.assertEqual(worker.get_redirect_history_from_task(task, 10), (is_input, output))
