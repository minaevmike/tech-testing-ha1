import unittest
import mock
from notification_pusher import *



class NotificationPusherTestCase(unittest.TestCase):

    def test_notification_worker_ack_succ(self):

        task = mock.Mock()
        data = {'callback_url': '://'}
        task.data.copy = mock.Mock(return_value = data)


        task_queue = mock.MagicMock()
        response = mock.Mock()
        response.status_code = 200

        with mock.patch('requests.post', mock.Mock(return_value = response)), mock.patch.object(json, 'dumps', mock.Mock()):
            notification_worker(task, task_queue)

        task_queue.put.assert_called_with((task, 'ack'))


    def test_notification_worker_ack_bury(self):

        task = mock.Mock()
        data = {'callback_url': '://'}
        task.data.copy = mock.Mock(return_value = data)


        task_queue = mock.MagicMock()

        with mock.patch('requests.post', mock.Mock(side_effect = requests.RequestException('EBury'))), mock.patch.object(json, 'dumps', mock.Mock()):
            notification_worker(task, task_queue)

        task_queue.put.assert_called_with((task, 'bury'))


    def test_done_with_processed_tasks_succ(self):
        task = mock.Mock()
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(return_value = (task, 'action'))

        m_logger = mock.MagicMock()
        with mock.patch('notification_pusher.logger', m_logger):
            done_with_processed_tasks(task_queue)
        self.assertFalse(m_logger.exception.called)


    def test_done_with_processed_tasks_getattr_fail(self):
        task = mock.Mock()
        task.action = mock.Mock(side_effect = tarantool.DatabaseError())
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(return_value = (task, 'action'))

        m_logger = mock.MagicMock()
        with mock.patch('notification_pusher.logger', m_logger):
            done_with_processed_tasks(task_queue)
        self.assertTrue(m_logger.exception.called)


    def test_done_with_processed_tasks_empty_list(self):
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(side_effect = gevent.queue.Empty)

        d_logger = mock.MagicMock()
        with mock.patch('notification_pusher.logger.debug', d_logger):
            done_with_processed_tasks(task_queue)
        d_logger.assert_any_call('gevent_queue.Empty')


    pass