"""
Library for helping SDK implementations
Version 0.2
"""

try:
    # Try to use the new Python3 HTTP library if available
    import http.client as http
    from urllib.parse import urlencode
except:
    # Must be using Python2 so use the appropriate library
    import httplib as http
    from urllib import urlencode

import ssl
import sys
import json
import collections

from .util.urlvalidator import urlsplit
from .util.decorators import deprecated
from .util.file import get_filename_stream


class SdkResponse(object):

    def __init__(self, data):
        try:
            self.data = json.loads(data)
        except ValueError:
            self.data = data

    def get_data(self):
        return self.data


class SdkBase(object):
    """

    """

    API_HOST = "127.0.0.1"
    API_PORT = 80
    API_SCHEME = "http"
    API_PROXY = None
    API_PROXY_PORT = 8080

    USER_AGENT_HEADER_NAME = "User-Agent"
    PRAGMA_HEADER_NAME = "Pragma"
    CONTENT_TYPE_HEADER_NAME = "Content-Type"
    CONTENT_LENGTH_HEADER_NAME = "Content-Length"
    ACCEPT_HEADER_NAME = "Accept"
    ACCEPT_LANGUAGE_HEADER_NAME = "Accept-Language"
    ACCEPT_ENCODING_HEADER_NAME = "Accept-Encoding"
    CACHE_CONTROL_HEADER_NAME = "Cache-Control"
    CONNECTION_HEADER_NAME = "Connection"
    REFERRER_HEADER_NAME = "Referer"


    CONTENT_TYPE_JSON = "application/json"
    CONTENT_TYPE_OCTET = "application/octet-stream"
    CONTENT_TYPE_PLAIN_TEXT = "text/plain; charset=utf-8"

    @classmethod
    def set_host(cls, hostname):
        """
        Set hostname.
        @param $host The host to be connected with, e.g. (http://hostname) or (https://X.X.X.X:port)
        """
        scheme, host, port = urlsplit(hostname)
        if scheme == 'http':
            cls.API_SCHEME = scheme
            cls.API_PORT = 80
        elif scheme == 'https':
            cls.API_SCHEME = scheme
            cls.API_PORT = 443
        if port:
            cls.API_PORT = port
        cls.API_HOST = host

    @classmethod
    def set_proxy(cls, proxy):
        """
        Set up proxy.
        @param $proxy The proxy server to be connected with, e.g. (http://hostname) or (https://hostname)
        """
        _, host, port = urlsplit(proxy)
        if port:
            cls.API_PROXY_PORT = port
        cls.API_PROXY = host

    @staticmethod
    def encode_multipart_formdata(fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name=%s' % key)
            L.append('Content-Type: %s' % SdkBase.CONTENT_TYPE_JSON)
            L.append('')
            L.append(str(value))
        for (key, value) in files:
            filename, stream = get_filename_stream(value)
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name=%s; filename=%s' % (key, filename))
            L.append('Content-Type: %s' % SdkBase.CONTENT_TYPE_OCTET)
            L.append('')
            L.append(stream)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def default_headers(self):
        return dict()

    def _http(self, method, url, headers=None, form_params=None, query_params=None, ssl_verified=False,
              form_urlencoding=True):
        """
        Internal method to do http requests.
        :param method:
        :param url:
        :param headers:
        :param form_params:
        :param query_params:
        :param ssl_verified:
        :param form_urlencoding:
        :return:
        """
        context = None

        if headers is not None:
            xHeaders = headers
        else:
            xHeaders = self.default_headers()

        if self.API_SCHEME == 'https':
            if sys.version_info[0:3] >= (2,7,9) or sys.version_info[0:3] >= (3,4,3):
                if not ssl_verified:
                    context = ssl._create_unverified_context()
                if self.API_PROXY:
                    conn = http.HTTPSConnection(self.API_PROXY, self.API_PROXY_PORT, context=context)
                    conn.set_tunnel(self.API_HOST, self.API_PORT)
                else:
                    conn = http.HTTPSConnection(self.API_HOST, self.API_PORT, context=context)
            else:
                if self.API_PROXY:
                    conn = http.HTTPSConnection(self.API_PROXY, self.API_PROXY_PORT)
                    conn.set_tunnel(self.API_HOST, self.API_PORT)
                else:
                    conn = http.HTTPSConnection(self.API_HOST, self.API_PORT)
        else:
            if self.API_PROXY:
                conn = http.HTTPConnection(self.API_PROXY, self.API_PROXY_PORT)
                url = "http://" + self.API_HOST + ":" + str(self.API_PORT) + url
            else:
                conn = http.HTTPConnection(self.API_HOST, self.API_PORT)

        if (method == "POST" or method == "PUT") and form_urlencoding:
            xHeaders["Content-Type"] = "application/x-www-form-urlencoded"

        if query_params:
            url += "?%s" % (urlencode(query_params))

        if form_params and form_urlencoding:
            parameters = urlencode(form_params)
            conn.request(method, url, parameters, headers=xHeaders)
        elif form_params and isinstance(form_params, collections.Mapping):
            parameters = json.dumps(form_params)
            conn.request(method, url, parameters, headers=xHeaders)
        elif form_params:
            parameters = form_params
            conn.request(method, url, parameters, headers=xHeaders)
        else:
            conn.request(method, url, headers=xHeaders)

        response = conn.getresponse()

        status = response.status
        resHeaders = response.getheaders()
        resData = response.read()
        #resData = response.read().encode('utf-8')

        conn.close()

        return status, resData, dict(resHeaders)


@deprecated
def parse_params(vars):
    to_return = dict()
    for elem in vars:
        if vars[elem] is not None:
            to_return[elem] = vars[elem]
    return to_return


@deprecated
def parse_args(**kwargs):
    to_return = dict()
    for elem in kwargs:
        if kwargs[elem] is not None:
            to_return[elem] = kwargs[elem]
    return to_return


@deprecated
def safe_add_slash(item):
    if item is not None:
        to_return = "/" + str(item)
    else:
        to_return = ""
    return to_return