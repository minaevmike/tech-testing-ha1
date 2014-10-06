import unittest
import mock
from source import redirect_checker
from source.lib import utils
from argparse import Namespace

def check_stop(*arg):
    redirect_checker.is_run = False

def check_start(*arg):
    redirect_checker.is_run = True

class RedirectCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self.config = utils.Config()

    @mock.patch('source.redirect_checker.sleep', mock.Mock(side_effect=check_stop))
    def test_main_loop_check_network_status_ok_with_good_number_of_workres(self):
        pid = 50
        children_mock = mock.Mock()
        setattr(self.config, "SLEEP", 1)
        setattr(self.config, "WORKER_POOL_SIZE", 10)
        setattr(self.config, "CHECK_URL", "URL")
        setattr(self.config, "HTTP_TIMEOUT", 20)
        with mock.patch('os.getpid', mock.Mock(return_value=pid)):
            with mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=[children_mock])):
                with mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True)):
                    with mock.patch('source.redirect_checker.spawn_workers', mock.Mock()) as spworkd:
                        redirect_checker.main_loop(self.config)

        assert spworkd.called


    @mock.patch('source.redirect_checker.sleep', mock.Mock(side_effect=check_stop))
    def test_main_loop_check_network_status_ok_with_bad_number_of_workres(self):
        pid = 50
        children_mock = mock.Mock()
        setattr(self.config, "SLEEP", 1)
        setattr(self.config, "WORKER_POOL_SIZE", 0)
        setattr(self.config, "CHECK_URL", "URL")
        setattr(self.config, "HTTP_TIMEOUT", 20)
        with mock.patch('os.getpid', mock.Mock(return_value=pid)):
            with mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=[children_mock])):
                with mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True)):
                    with mock.patch('source.redirect_checker.spawn_workers', mock.Mock()) as spworkd:
                        redirect_checker.main_loop(self.config)

        assert not spworkd.called

    @mock.patch('source.redirect_checker.sleep', mock.Mock(side_effect=check_stop))
    def test_main_loop_check_network_status_fail(self):
        pid = 50
        children_mock = mock.Mock()
        setattr(self.config, "SLEEP", 1)
        setattr(self.config, "WORKER_POOL_SIZE", 10)
        setattr(self.config, "CHECK_URL", "URL")
        setattr(self.config, "HTTP_TIMEOUT", 20)
        with mock.patch('os.getpid', mock.Mock(return_value=pid)):
            with mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=[children_mock])):
                with mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=False)):
                    redirect_checker.main_loop(self.config)

        assert children_mock.terminate.called

    def test_main_with_daemon_and_pidfile(self):
        exitcode = 100550
        setattr(self.config, "LOGGING", {"version": 1})
        setattr(self.config, "EXIT_CODE", exitcode)
        with mock.patch('source.redirect_checker.daemonize', mock.Mock()) as daemon:
            with mock.patch('source.redirect_checker.main_loop', mock.Mock()) as main_loop:
                with mock.patch('source.redirect_checker.load_config_from_pyfile', mock.Mock(return_value=self.config)):
                    with mock.patch('os.path', mock.MagicMock(return_value=self.config)):
                        with mock.patch('source.redirect_checker.parse_cmd_args', mock.Mock(return_value=Namespace(daemon=True, pidfile=1, config=self.config))):
                            with mock.patch('source.redirect_checker.create_pidfile', mock.Mock()) as pidfile:
                                assert redirect_checker.main([]) == exitcode, "Exit code not same"
        assert daemon.called, "Daemon doesn't called"
        assert pidfile.called, "create pid file doens't call"

    def test_main_with_no_daemon(self):
        setattr(self.config, "LOGGING", {"version": 1})
        setattr(self.config, "EXIT_CODE", 0)
        with mock.patch('source.redirect_checker.daemonize', mock.Mock()) as daemon:
            with mock.patch('source.redirect_checker.main_loop', mock.Mock()) as main_loop:
                with mock.patch('source.redirect_checker.load_config_from_pyfile', mock.Mock(return_value=self.config)):
                    with mock.patch('os.path', mock.MagicMock(return_value=self.config)):
                        with mock.patch('source.redirect_checker.parse_cmd_args', mock.Mock(return_value=Namespace(daemon=False, pidfile=None, config=self.config))):
                            with mock.patch('source.redirect_checker.create_pidfile', mock.Mock()) as pidfile:
                                redirect_checker.main([])
        assert not daemon.called, "Daemon called, but it shouldn't"
        assert not pidfile.called, "Create pidfile called, but it shouldn't"
    def tearDown(self):
        check_start()