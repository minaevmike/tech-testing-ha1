import json
import requests
import tarantool
import tarantool_queue
import unittest
import gevent
import mock
from argparse import Namespace
from source import notification_pusher

def stop_notification_pusher(*smth):
    notification_pusher.run_application = False


class NotificationPusherTestCase(unittest.TestCase):
    def setUp(self):
            notification_pusher.logger = mock.MagicMock()
            self.config = mock.MagicMock()
            setattr(self.config, "LOGGING", {"version": 1})
            setattr(self.config, "WORKER_POOL_SIZE", 10)
            notification_pusher.parse_cmd_args = mock.Mock()
    def test_notification_worker_ack_succ(self):
        task = mock.Mock()
        data = {'callback_url': '://'}
        task.data.copy = mock.Mock(return_value = data)

        task_queue = mock.MagicMock()
        response = mock.Mock()
        response.status_code = 200

        with mock.patch('requests.post', mock.Mock(return_value = response)), mock.patch('json.dumps', mock.Mock()):
            notification_pusher.notification_worker(task, task_queue)

        task_queue.put.assert_called_with((task, 'ack'))


    def test_notification_worker_ack_bury(self):
        task = mock.Mock()
        data = {'callback_url': '://'}
        task.data.copy = mock.Mock(return_value = data)

        task_queue = mock.MagicMock()

        with mock.patch('requests.post', mock.Mock(side_effect = requests.RequestException('EBury'))),\
             mock.patch('notification_pusher.logger', mock.Mock()),\
             mock.patch('json.dumps', mock.Mock()):
                notification_pusher.notification_worker(task, task_queue)

        task_queue.put.assert_called_with((task, 'bury'))


    def test_done_with_processed_tasks_succ(self):
        task = mock.Mock()
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value=1)
        task_queue.get_nowait = mock.Mock(return_value=(task, 'action'))

        m_logger = mock.MagicMock()
        with mock.patch('notification_pusher.logger', m_logger):
            notification_pusher.done_with_processed_tasks(task_queue)
        self.assertFalse(m_logger.exception.called)


    def test_done_with_processed_tasks_getattr_fail(self):
        action_name = "action"
        error = "error"
        task = mock.Mock()
        task.action = mock.Mock(side_effect=tarantool.DatabaseError(error))

        queue = gevent.queue.Queue()
        queue.qsize = mock.Mock(return_value=1)
        queue.get_nowait = mock.Mock(return_value=(task, action_name))

        notification_pusher.done_with_processed_tasks(queue)
        assert notification_pusher.logger.exception.called

    def test_done_with_processed_tasks_empty_list(self):
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value=1)
        task_queue.get_nowait = mock.Mock(side_effect=gevent.queue.Empty)

        m_logger = mock.MagicMock()
        with mock.patch('notification_pusher.logger.debug', m_logger) as logger:
            notification_pusher.done_with_processed_tasks(task_queue)
        logger.assert_any_call_('gevent_queue.Empty')


    def test_stop_handler_succ(self):
        notification_pusher.run_application = True
        notification_pusher.stop_handler(notification_pusher.exit_code)
        self.assertTrue(notification_pusher.run_application == False)


    def test_main_loop_no_run(self):
        queue = mock.Mock(name="queue")
        queue.tube().take = mock.Mock(return_value=None)
        tarantool_queue.Queue = mock.Mock(return_value=queue)

        with mock.patch('source.notification_pusher.sleep',
                        stop_notification_pusher),\
             mock.patch('source.notification_pusher.Greenlet',
                        mock.Mock()) as creation:
            notification_pusher.main_loop(self.config)

        assert not creation.called

    def test_install_signal_handlers_succ(self):
        m_signal = mock.MagicMock()
        with mock.patch('gevent.signal', m_signal):
            notification_pusher.install_signal_handlers()
        self.assertTrue(m_signal.call_count == len(notification_pusher.SIGNALS))


    # def test_main_succ_without_run(self):
    #     m_daemonize = mock.Mock()
    #     m_create_pidfile = mock.Mock()
    #     m_logger = mock.Mock()
    #     main_runner(m_daemonize, m_create_pidfile, m_logger, ['','-c', './source/config/pusher_config.py'])
    #
    #     self.assertFalse(m_daemonize.called)
    #     self.assertFalse(m_create_pidfile.called)
    #     self.assertTrue(m_logger.info.called)
    #
    # def test_main_daemon_succ(self):
    #     m_daemonize = mock.Mock()
    #     m_create_pidfile = mock.Mock()
    #     m_logger = mock.Mock()
    #     main_runner(m_daemonize, m_create_pidfile, m_logger, ['','-d','-c', './source/config/pusher_config.py'])
    #
    #     self.assertTrue(m_daemonize.called)
    #     self.assertFalse(m_create_pidfile.called)
    #     self.assertTrue(m_logger.info.called)
    #
    # def test_main_pidfile_succ(self):
    #     m_daemonize = mock.Mock()
    #     m_create_pidfile = mock.Mock()
    #     m_logger = mock.Mock()
    #     main_runner(m_daemonize, m_create_pidfile, m_logger, ['','-c', './source/config/pusher_config.py', '-P', '0'])
    #
    #     self.assertFalse(m_daemonize.called)
    #     self.assertTrue(m_create_pidfile.called)
    #     self.assertTrue(m_logger.info.called)
    #
    #
    # def test_main_run_succ(self):
    #     m_main_loop = mock.Mock()
    #     with mock.patch('notification_pusher.main_loop', m_main_loop):
    #          main_runner(mock.Mock(), mock.Mock(), mock.Mock(), ['','-c', './source/config/pusher_config.py'])
    #
    #     m_main_loop.assert_called_once()
    #
    #
    # def test_main_run_fail(self):
    #     m_main_loop = mock.Mock(side_effect = Exception("E"))
    #     m_logger = mock.Mock()
    #     notification_pusher.run_application = True
    #     with mock.patch('notification_pusher.sleep', mock.Mock(side_effect = stop_notification_pusher)),\
    #          mock.patch('notification_pusher.logger', m_logger),\
    #          mock.patch('notification_pusher.main_loop', m_main_loop):
    #          main_runner(mock.Mock(), mock.Mock(), m_logger, ['','-c', './source/config/pusher_config.py'], run = True)
    #
    #     self.assertTrue(m_logger.error.called)
    #



    pass