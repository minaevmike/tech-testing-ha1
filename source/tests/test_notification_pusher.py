import unittest
import mock
from notification_pusher import *
import notification_pusher


class NotificationPusherTestCase(unittest.TestCase):

    def test_notification_worker_ack_succ(self):

        task = mock.Mock()
        data = {'callback_url': '://'}
        task.data.copy = mock.Mock(return_value=data)


        task_queue = mock.MagicMock()
        response = mock.Mock(return_value={'status_code': 200})

        with mock.patch('requests.post', mock.Mock(return_value=response)), mock.patch.object(json, 'dumps', mock.Mock()):
            notification_worker(task, task_queue)

        task_queue.put.assert_called_with((task, 'ack'))

    pass