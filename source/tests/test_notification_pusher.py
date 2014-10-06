from argparse import Namespace
import unittest
import mock
from notification_pusher import *
import notification_pusher
from tarantool_queue import Queue

def stop_notification_pusher(*smth):
    notification_pusher.run_application = False

def make_conf():
    config = mock.Mock()
    config.QUEUE_HOST = '0.0.0.0'
    config.QUEUE_PORT = 1234
    config.QUEUE_SPACE = 0
    config.WORKER_POOL_SIZE = 1
    config.QUEUE_TAKE_TIMEOUT = 100
    config.SLEEP_ON_FAIL = 0
    return config

def main_runner(daem, create_pf, logger, args, run = False):
    config = make_conf()
    notification_pusher.run_application = run
    with mock.patch('notification_pusher.logger', logger),\
         mock.patch('notification_pusher.patch_all', mock.Mock()),\
         mock.patch('notification_pusher.daemonize', daem),\
         mock.patch('notification_pusher.create_pidfile', create_pf),\
         mock.patch('source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value = config)): #WTF I need source. here?
                main(args)


class NotificationPusherTestCase(unittest.TestCase):
    def setUp(self):
        self.old_logger_info = notification_pusher.logger.info
        notification_pusher.logger.info = mock.Mock()


    def test_notification_worker_ack_succ(self):
        task = mock.Mock()
        data = {'callback_url': '://'}
        task.data.copy = mock.Mock(return_value = data)

        task_queue = mock.MagicMock()
        response = mock.Mock()
        response.status_code = 200

        with mock.patch('requests.post', mock.Mock(return_value = response)), mock.patch('json.dumps', mock.Mock()):
            notification_worker(task, task_queue)

        task_queue.put.assert_called_with((task, 'ack'))


    def test_notification_worker_ack_bury(self):
        task = mock.Mock()
        data = {'callback_url': '://'}
        task.data.copy = mock.Mock(return_value = data)

        task_queue = mock.MagicMock()

        with mock.patch('requests.post', mock.Mock(side_effect = requests.RequestException('EBury'))),\
             mock.patch('notification_pusher.logger', mock.Mock()),\
             mock.patch('json.dumps', mock.Mock()):
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

        m_logger = mock.MagicMock()
        with mock.patch('notification_pusher.logger.debug', m_logger):
            done_with_processed_tasks(task_queue)
        m_logger.assert_any_call('gevent_queue.Empty')


    def test_stop_handler_succ(self):
        notification_pusher.run_application = True
        stop_handler(exit_code)
        self.assertTrue(notification_pusher.run_application == False)


    def test_mainloop_conf_succ(self):
        config = make_conf()

        queue = mock.Mock(side_effect = stop_notification_pusher)
        done = mock.MagicMock()
        with mock.patch('gevent.queue.Queue', queue), mock.patch('notification_pusher.done_with_processed_tasks', done):
            main_loop(config)
        done.assert_called_once()


    def test_mainloop_worker_fail(self):
        config = make_conf()
        config.WORKER_POOL_SIZE = 0

        taker = mock.MagicMock()
        with mock.patch('tarantool_queue.tarantool_queue.Tube.take', taker):
            main_loop(config)
        self.assertFalse(taker.called)


    def test_mainloop_worker_succ(self):
        config = make_conf()

        taker = mock.Mock()
        worker = mock.Mock()
        with mock.patch('tarantool_queue.tarantool_queue.Tube.take', taker),\
             mock.patch('gevent.Greenlet', mock.Mock(return_value = worker)):
            main_loop(config)
        self.assertFalse(taker.called)
        worker.start.assert_called_once()


    def test_mainloop_app_no_run(self):
        config = make_conf()
        m_logger_info = mock.MagicMock()
        notification_pusher.run_application = False
        with mock.patch('notification_pusher.logger.info', m_logger_info):
            main_loop(config)
        m_logger_info.assert_called_with(STOP_APPLICATION_LOOT_STR)
        notification_pusher.run_application = True


    def test_install_signal_handlers_succ(self):
        m_signal = mock.MagicMock()
        with mock.patch('gevent.signal', m_signal):
            install_signal_handlers()
        self.assertTrue(m_signal.call_count == len(SIGNALS))


    def test_main_succ_without_run(self):
        m_daemonize = mock.Mock()
        m_create_pidfile = mock.Mock()
        m_logger = mock.Mock()

        main_runner(m_daemonize, m_create_pidfile, m_logger, ['','-c', './source/config/pusher_config.py'])

        self.assertFalse(m_daemonize.called)
        self.assertFalse(m_create_pidfile.called)
        self.assertTrue(m_logger.info.called)


    def test_main_daemon_succ(self):
        m_daemonize = mock.Mock()
        m_create_pidfile = mock.Mock()
        m_logger = mock.Mock()
        main_runner(m_daemonize, m_create_pidfile, m_logger, ['','-d','-c', './source/config/pusher_config.py'])

        self.assertTrue(m_daemonize.called)
        self.assertFalse(m_create_pidfile.called)
        self.assertTrue(m_logger.info.called)


    def test_main_pidfile_succ(self):
        m_daemonize = mock.Mock()
        m_create_pidfile = mock.Mock()
        m_logger = mock.Mock()
        main_runner(m_daemonize, m_create_pidfile, m_logger, ['','-c', './source/config/pusher_config.py', '-P', '0'])

        self.assertFalse(m_daemonize.called)
        self.assertTrue(m_create_pidfile.called)
        self.assertTrue(m_logger.info.called)


    def test_main_run_succ(self):
        m_main_loop = mock.Mock(side_effect = stop_notification_pusher)
        with mock.patch('notification_pusher.main_loop', m_main_loop):
             main_runner(mock.Mock(), mock.Mock(), mock.Mock(), ['','-c', './source/config/pusher_config.py'], run = True)

        m_main_loop.assert_called_once()


    def test_main_run_fail(self):
        m_main_loop = mock.Mock(side_effect = Exception("E"))
        m_logger = mock.Mock()
        notification_pusher.run_application = True
        with mock.patch('notification_pusher.sleep', mock.Mock(side_effect = stop_notification_pusher)),\
             mock.patch('notification_pusher.logger', m_logger),\
             mock.patch('notification_pusher.main_loop', m_main_loop):
             main_runner(mock.Mock(), mock.Mock(), m_logger, ['','-c', './source/config/pusher_config.py'], run = True)

        self.assertTrue(m_logger.error.called)




    pass