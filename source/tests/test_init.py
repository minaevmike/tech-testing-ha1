__author__ = 'Mike'
import unittest
#import lib.__init__ as init
import test_html as html
import mock
from source.lib import to_str, to_unicode, get_counters, check_for_meta, fix_market_url, make_pycurl_request, \
    get_url, REDIRECT_HTTP, REDIRECT_META, get_redirect_history, prepare_url
class UnitTestCase(unittest.TestCase):
    def test_unicode_to_unicode(self):
        string = u"test string !;;''"
        assert isinstance(to_unicode(string), unicode)

    def test_not_unicode_to_unicode(self):
        string = "test string !;;''"
        assert isinstance(to_unicode(string), unicode)

    def test_string_to_string(self):
        string = "test string !;;''"
        assert isinstance(to_str(string), str)

    def test_unicode_to_string(self):
        string = u"test string !;;''"
        assert isinstance(to_str(string), str)

    def test_get_counters_empty(self):
        counters = get_counters("")
        assert not counters

    def test_get_counters_google(self):
        assert get_counters(html.site_with_google_analitcs()) == ['GOOGLE_ANALYTICS']

    def test_meta_empty(self):
        self.assertEqual(check_for_meta(html.blank_site(), "google.com"), None)

    def test_meta_bad_content_length_in_meta(self):
        self.assertEqual(check_for_meta(html.bad_content_length_in_meta_tag(), "google.com"), None)

    def test_meta_bad_content_url_in_meta(self):
        self.assertEqual(check_for_meta(html.bad_content_url_in_meta_tag(), "google.com"), None)

    def test_meta_bad_http_equiv_in_meta(self):
        self.assertEqual(check_for_meta(html.no_http_equiv_in_meta_tag(), "google.com"), None)

    def test_meta_bad(self):
        url = 'google.com'
        self.assertEqual(check_for_meta(html.good_meta_tag(), url), url)

    def test_fix_market_url(self):
        market_url = 'market://details?id=<package_name>'
        http_url = 'http://play.google.com/store/apps/details?id=<package_name>'
        self.assertEqual(fix_market_url(market_url), http_url)

    def test_make_pycurl_request(self):
        mock_Curl = mock.MagicMock()
        mock_StringIO = mock.MagicMock()
        with mock.patch('pycurl.Curl', mock_Curl),\
                mock.patch('source.lib.StringIO', mock_StringIO):
            mock_Curl().getinfo.return_value = None
            mock_StringIO().getvalue.return_value = 'Content'
            a = make_pycurl_request('http://example.ru/', 10)
            self.assertEqual(a, ('Content', None))

    def test_make_curl_request(self):
        content = "VK.com"
        redirect_url = u"abc"
        mock_curl = mock.MagicMock()
        mock_curl.getinfo = mock.Mock(return_value=redirect_url)
        mock_curl.setopt = mock.Mock()
        mock_io_string = mock.MagicMock()
        mock_io_string.getvalue = mock.Mock(return_value=content)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=mock_io_string)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=mock_curl)):
                with mock.patch('source.lib.to_str', mock.Mock()):
                        with mock.patch('source.lib.prepare_url', mock.Mock()):
                            self.assertEqual(make_pycurl_request('http://test.rg', 10), (content, redirect_url))

    def test_make_curl_request_with_useragetn(self):
        content = "VK.com"
        redirect_url = u"abc"
        userageng = "Agent"
        mock_curl = mock.MagicMock()
        mock_curl.getinfo = mock.Mock(return_value=redirect_url)
        mock_io_string = mock.MagicMock()
        mock_io_string.getvalue = mock.Mock(return_value=content)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=mock_io_string)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=mock_curl)) as c_mock:
                with mock.patch('source.lib.to_str', mock.Mock()):
                        with mock.patch('source.lib.prepare_url', mock.Mock()):
                            self.assertEqual(make_pycurl_request('http://test.rg', 10, userageng), (content, redirect_url))
                            c_mock().setopt.assert_any_call(c_mock().USERAGENT, userageng)

    def test_make_curl_request_without_redirect(self):
        content = "VK.com"
        mock_curl = mock.MagicMock()
        mock_curl.setopt = mock.Mock()
        mock_curl.getinfo = mock.Mock(return_value=None)

        mock_io_string = mock.MagicMock()
        mock_io_string.getvalue = mock.Mock(return_value=content)

        with mock.patch('source.lib.StringIO', mock.Mock(return_value=mock_io_string)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=mock_curl)):
                with mock.patch('source.lib.prepare_url', mock.Mock()):
                    self.assertEqual(make_pycurl_request('http://test.rg', 10), (content, None))

    def test_get_url_with_error_on_make_curl_request(self):
        url = "abc"
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            self.assertEqual(get_url(url, 10, "A"), (url, 'ERROR', None))

    def test_get_url_with_match_ok_redirect(self):
        contnent = "VK.COM"
        redirect = "a"
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(contnent, redirect))):
            with mock.patch('source.lib.OK_REDIRECT', mock.Mock()):
                with mock.patch('source.lib.OK_REDIRECT.match', mock.Mock(return_value=True)):
                    self.assertEqual(get_url("abc", 10, "A"), (None, None, contnent))

    def test_get_url_with_http_redirect(self):
        contnent = "VK.COM"
        redirect = "a"
        url = "abc"
        market = mock.Mock()
        market.scheme = 'market'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(contnent, redirect))):
            with mock.patch('source.lib.OK_REDIRECT', mock.Mock()):
                with mock.patch('source.lib.OK_REDIRECT.match', mock.Mock(return_value=False)):
                    with mock.patch('source.lib.urlsplit', mock.Mock(return_value=market)):
                        with mock.patch('source.lib.fix_market_url', mock.Mock(return_value=url)):
                            with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
                                self.assertEqual(get_url(url, 10, "A"), (url, REDIRECT_HTTP, contnent))


    def test_get_url_with_meta_redirect(self):
        contnent = "VK.COM"
        url = "abc"
        market = mock.Mock()
        market.scheme = 'http'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(contnent, None))):
            with mock.patch('source.lib.OK_REDIRECT', mock.Mock()):
                with mock.patch('source.lib.OK_REDIRECT.match', mock.Mock(return_value=False)):
                    with mock.patch('source.lib.urlsplit', mock.Mock(return_value=market)):
                        with mock.patch('source.lib.fix_market_url', mock.Mock(return_value=url)):
                            with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
                                with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=url)):
                                    self.assertEqual(get_url(url, 10, "A"), (url, REDIRECT_META, contnent))

    def test_get_url_with_no_http_and_meta_redirect(self):
        contnent = "VK.COM"
        url = "abc"
        market = mock.Mock()
        market.scheme = 'http'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(contnent, None))):
            with mock.patch('source.lib.OK_REDIRECT', mock.Mock()):
                with mock.patch('source.lib.OK_REDIRECT.match', mock.Mock(return_value=False)):
                    with mock.patch('source.lib.urlsplit', mock.Mock(return_value=market)):
                        with mock.patch('source.lib.fix_market_url', mock.Mock(return_value=url)):
                            with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
                                with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=None)):
                                    self.assertEqual(get_url(url, 10, "A"), (url, None, contnent))

    def test_get_redirect_history_for_mm(self):
        url = 'http://my.mail.ru/apps/'
        self.assertEqual(get_redirect_history(url, 10), ([], [url], []))

    def test_get_redirect_history_for_od(self):
        url = 'http://www.odnoklassniki.ru/someapp'
        self.assertEqual(get_redirect_history(url, 10), ([], [url], []))

    def test_get_regirect_history_repeat(self):
        urlg = 'http://example.com'
        url = ('http://test.org', REDIRECT_HTTP, None)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            self.assertEqual(get_redirect_history(urlg, 10), ([url[1], url[1]], [urlg, url[0], url[0]], []))

    def test_get_redirect_history_overlimut(self):
        urlg = 'http://example.com'
        url = ('http://test.org', REDIRECT_HTTP, None)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            self.assertEqual(get_redirect_history(urlg, 10, 1), ([url[1]], [urlg, url[0]], []))

    def test_get_redirect_no_redirect_url(self):
        urlg = 'http://example.com'
        url = (None, REDIRECT_HTTP, None)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            self.assertEqual(get_redirect_history(urlg, 10), ([], [urlg], []))

    def test_get_redirect_error_redirect_type(self):
        urlg = 'http://example.com'
        url = ('http://test.org', 'ERROR', None)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            self.assertEqual(get_redirect_history(urlg, 10), ([url[1]], [urlg, url[0]], []))

    def test_get_redirect_with_counter(self):
        urlg = 'http://example.com'
        content = 'Content'
        counter = 'counter'
        url = ('http://test.org', REDIRECT_HTTP, content)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_counters', mock.Mock(return_value='counter')):
                self.assertEqual(get_redirect_history(urlg, 10, 1), ([url[1]], [urlg, url[0]], counter))

    def test_prepare_url_none(self):
        url = None
        self.assertEqual(prepare_url(url), None)

    def test_prepare_url_good(self):
        url = """http://test.com/a b#'?tr=tee"""
        self.assertEqual(prepare_url(url), """http://test.com/a%20b%23'?tr=tee""")