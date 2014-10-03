__author__ = 'Mike'
import unittest
import mock
import source.lib.utils as utils


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

    #def test_load_config_from_py_file(self):
    #   config = {
    #        "A": "a",
    #        "B":{
    #            "C": "c",
    #            "D": "d",
    #        },
    #        "e": "E"
    #    }
    #    with mock.patch('source.lib.utils.exec_py', mock.Mock(return_value=config)):
    #        result = utils.load_config_from_pyfile('/path/to/file')
    #
    #    assert result["A"] == config["A"], "A from config doesn't equals to A from load_config"
    #    assert result["B"] == config["B"], "B from config doesn't equals to B from load_config"
    #    self.assertRaises(KeyError, result["e"])

