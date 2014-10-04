__author__ = 'Mike'
import unittest
import mock
import source.lib.utils as utils
import argparse
import urllib2


class UtilsTestCase(unittest.TestCase):

    def test_create_pidfile_ok(self):
        pid = 50
        m_open = mock.mock_open()
        with mock.patch('source.lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('/file/path')
        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_demonize_parent(self):
        pid = 50
        with mock.patch('os.fork', mock.Mock(return_value=pid)):
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                utils.daemonize()
        os_exit.assert_called_once_with(0)

    def test_demonize_child_parent(self):
        pid = 50
        with mock.patch('os.fork', mock.Mock(side_effect=[0, pid])):
            with mock.patch('os.setsid', mock.Mock()):
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    utils.daemonize()
        os_exit.assert_called_once_with(0)

    def test_demonize_child(self):
        pid = 0
        with mock.patch('os.fork', mock.Mock(return_value=pid)) as os_fork:
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                    utils.daemonize()
        assert os_fork.called, "os.fork don't called"
        assert os_setsid.called, "os.setsid don't called"
        assert not os_exit.called, "os._exit called, but it shouldn't"

    def test_demonize_failed_first_fork(self):
        with mock.patch('os.fork', mock.Mock(side_effect=OSError("Error"))):
            self.assertRaises(Exception, utils.daemonize)

    def test_demonize_failed_second_fork(self):
        with mock.patch('os.fork', mock.Mock(side_effect=[0, OSError("Error")])):
            with mock.patch('os.setsid', mock.Mock()):
                self.assertRaises(Exception, utils.daemonize)

    def test_load_config_from_py_file(self):
        result = utils.load_config_from_pyfile('source/tests/test_conf.py')
        assert getattr(result, 'GOOD_FIELD') == 'a', "Can't read good field"
        self.assertRaises(AttributeError, getattr, result, 'bad_field')

    def test_parse_cmd_args(self):
        args = ["-c", "config", "-d"]
        parsed_args = utils.parse_cmd_args(args)
        self.assertEqual(argparse.Namespace(config='config', daemon=True, pidfile=None), parsed_args)

    def test_check_network_status_ok(self):
        with mock.patch('urllib2.urlopen', mock.Mock()):
            assert utils.check_network_status("URL", 0)

    def test_check_network_status_fail(self):
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=urllib2.URLError('AAA'))):
            assert not utils.check_network_status("URL", 0)

    def test_spawn_workers_none(self):
        process = mock.Mock()
        with mock.patch('multiprocessing.Process', mock.Mock(return_value=process)):
            utils.spawn_workers(0, "AAA", [], 0)
            assert not process.called

    def test_spawn_workers_called_n_times(self):
        n = 10
        with mock.patch('source.lib.utils.Process', mock.Mock()) as process:
            utils.spawn_workers(n, "AAA", [], 0)
            assert process.call_count == n




