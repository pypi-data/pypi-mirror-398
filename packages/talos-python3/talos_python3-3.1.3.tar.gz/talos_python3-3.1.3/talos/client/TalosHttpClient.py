#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.thrift.auth.ttypes import Credential
from talos.thrift.auth import constants
from talos.thrift.transport.TTransport import TTransportBase
from talos.client.TalosErrors import TalosTransportError
from talos.client.TalosErrors import HttpStatusCode
from io import BytesIO
from datetime import datetime
from six.moves import urllib
from six.moves import http_client
from talos.utils.Utils import current_time_mills
import re
import six
import time
import hashlib
import hmac
import base64
import os
import ssl
import sys
import uuid
import logging
import dns.resolver
import random
import traceback
import IPy


class TalosHttpClientTransportFactory:

    _url = str
    _credential = Credential
    _client = http_client.HTTPConnection
    _clockOffset = int
    _agent = str

    def __init__(self, url=None, credential=None, client=None, agent=None):
        self._url = url
        self._credential = credential
        self._client = client
        self._agent = agent

    def get_transport(self, trans=None):
        return self.get_transport_with_clock_offset(trans, 0, "")

    def get_transport_with_clock_offset(self, trans=None, clockOffset=None, query=None):
        if trans:
            pass
        t2 = TalosHttpClient(uri_or_host=self._url, credential=self._credential, clockOffset=self._clockOffset, query=query)
        return t2


class TalosHttpClient(TTransportBase):
    logger = logging.getLogger("TalosHttpClient")
    GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
    _REQUEST_ID_LENGTH = 8
    _url_ = None
    _requestBuffer_ = BytesIO
    _inputStream_ = BytesIO()
    _connectTimeout_ = 0
    _socketTimeout_ = 0
    _clockOffset = 0
    _queryString = None
    _supportAccountKey = False
    _supportDnsResolver = False
    credential = Credential

    __http = None
    scheme = None
    using_proxy = None
    host = str
    port = None
    __timeout = None
    keyfile = None
    certfile = None
    context = None
    realhost = None
    realport = None
    proxy_auth = None
    path = None
    __http_response = None
    __wbuf = None
    __custom_headers = None
    __auth_headers = None
    code = None
    message = None
    _headers = dict()
    _uri_or_host = None
    _sid = None

    # def __init__(self, uri_or_host, credential: Credential, httpClient: http.client.HTTPConnection,
    #              agent: str, clockOffset: int, query: str):
    #     self._queryString = query
    #     self.__http = httpClient
    #     self.__init__(uri_or_host, credential, clockOffset, True)

    def __init__(self, uri_or_host, credential=None, clockOffset=None,
                 supportAccountKey=None, supportDnsResolver=None, port=None, path=None,
                 cafile=None, cert_file=None, key_file=None, ssl_context=None):
        """THttpClient supports two different types of construction:

        THttpClient(host, port, path) - deprecated
        THttpClient(uri, [port=<n>, path=<s>, cafile=<filename>, cert_file=<filename>, key_file=<filename>, ssl_context=<context>])

        Only the second supports https.  To properly authenticate against the server,
        provide the client's identity by specifying cert_file and key_file.  To properly
        authenticate the server, specify either cafile or ssl_context with a CA defined.
        NOTE: if both cafile and ssl_context are defined, ssl_context will override cafile.
        """
        if port is not None:
            self.logger.warning(
                "Please use the THttpClient('http{s}://host:port/path') constructor",
                DeprecationWarning,
                stacklevel=2)
            self.host = uri_or_host
            self.port = port
            assert path
            self.path = path
            self.scheme = 'http'
        else:
            parsed = urllib.parse.urlparse(uri_or_host)
            self.scheme = parsed.scheme
            assert self.scheme in ('http', 'https')
            if self.scheme == 'http':
                self.port = parsed.port or http_client.HTTPConnection.default_port
            elif self.scheme == 'https':
                self.port = parsed.port or http_client.HTTPConnection.default_port
                self.certfile = cert_file
                self.keyfile = key_file
                self.context = ssl.create_default_context(cafile=cafile) if (
                            cafile and not ssl_context) else ssl_context
            self.host = parsed.hostname
            self.path = parsed.path
            if parsed.query:
                self.path += '?%s' % parsed.query
        try:
            proxy = urllib.request.getproxies()[self.scheme]
        except KeyError:
            proxy = None
        else:
            if urllib.request.proxy_bypass(self.host):
                proxy = None
        if proxy:
            parsed = urllib.parse.urlparse(proxy)
            self.realhost = self.host
            self.realport = self.port
            self.host = parsed.hostname
            self.port = parsed.port
            self.proxy_auth = self.basic_proxy_auth_header(parsed)
        else:
            self.realhost = self.realport = self.proxy_auth = None
        self._clockOffset = clockOffset
        self._supportAccountKey = supportAccountKey
        self._supportDnsResolver = supportDnsResolver
        self.credential = credential
        self.__wbuf = BytesIO()
        self.__http_response = None
        self.__timeout = None
        self._uri_or_host = uri_or_host

    @staticmethod
    def basic_proxy_auth_header(proxy):
        if proxy is None or not proxy.username:
            return None
        ap = "%s:%s" % (urllib.parse.unquote(proxy.username),
                        urllib.parse.unquote(proxy.password))
        cr = base64.b64encode(ap).strip()
        return "Basic " + cr

    def using_proxy(self):
        return self.realhost is not None

    def set_timeout(self, ms):
        if ms is None:
            self.__timeout = None
        else:
            self.__timeout = int(ms / 1000.0)

    def set_custom_headers(self, headers):
        self.__custom_headers = headers

    def set_support_account_key(self, supportAccountKey=None):
        self._supportAccountKey = supportAccountKey

    # Set signature related headers when credential is properly set
    def set_authentication_headers(self, data=None):
        if self.credential:
            if self.credential.secretKey and self.credential.type:
                # signature is supported
                if constants.SIGNATURE_SUPPORT.get(self.credential.type):
                    # host
                    host = str(self.host)
                    host = host.split(":")[0]
                    self.__http.putheader(constants.HK_HOST, host)
                    self._headers[str(constants.HK_HOST).lower()] = host

                    # timestamp
                    timestamp = int(time.time()) + self._clockOffset
                    self.__http.putheader(constants.HK_TIMESTAMP, str(timestamp))
                    self._headers[str(constants.HK_TIMESTAMP).lower()] = str(timestamp)
                    mi_date = datetime.utcnow().strftime(self.GMT_FORMAT)
                    self.__http.putheader(constants.MI_DATE, mi_date)
                    self._headers[str(constants.MI_DATE).lower()] = mi_date

                    # content md5
                    m = hashlib.md5()
                    m.update(data)
                    data_md5 = m.hexdigest()
                    self.__http.putheader(constants.HK_CONTENT_MD5, data_md5)
                    self._headers[str(constants.HK_CONTENT_MD5).lower()] = data_md5

                    # signature
                    headers = dict()
                    for (k, v) in self._headers.items():
                        headers[str(k).lower()] = str(v)

                    # generate authString for header
                    try:
                        authType = "Galaxy-V2 "
                        if self._supportAccountKey:
                            authType = "Galaxy-V3 "
                        if self.credential.type == constants.UserType.APP_ACCESS_TOKEN:
                            authType = "OAuth "

                        # check secretKeyId and set header attached info
                        # secretKeyId format: "Service-Admin#SecretKeyId#developerId"
                        secretKeyId = self.credential.secretKeyId
                        if constants.HK_SERVICE_ADMIN in secretKeyId:
                            items = str(secretKeyId).split(constants.HK_SERVICE_MARK)
                            if not len(items) == 3:
                                raise RuntimeError("Invalid credential secretKeyId, " + \
                                                   "expected: 3, actual: " + str(len(items)))
                            #  reset secretKeyId and add header attached info
                            secretKeyId = items[0]
                            self.__http.putheader(constants.HK_ATTACHED_INFO, items[2])
                            self._headers[str(constants.HK_ATTACHED_INFO).lower()] = items[2]

                        authString = authType + secretKeyId + ":"
                        authString += self.generate_auth_header(self._headers, self.canonicalize_resource(self._uri_or_host))
                        self.__http.putheader(constants.HK_AUTHORIZATION, authString)
                        self._headers[str(constants.HK_AUTHORIZATION).lower()] = authString
                    except Exception as e:
                        self.logger.error("fail to sign" + str(traceback.format_exc()))
            else:
                if self.credential.type == constants.UserType.APP_XIAOMI_SSO:
                    authString = "SSO " + self._sid + ":" + self.credential.secretKey + ":" + self.credential.secretKeyId
                    self.__http.putheader(constants.HK_AUTHORIZATION, authString)
                elif self.credential.type == constants.UserType.APP_ANONYMOUS:
                    authString = "Guest " + self.credential.secretKeyId
                    self.__http.putheader(constants.HK_AUTHORIZATION, authString)
                else:
                    raise RuntimeError("Unsupported user type: " + self.credential.type)
            return

    def generate_auth_header(self, headers=None, canonicalizeResource=None):
        stringToSign = "POST\n"
        if "content-md5" in headers:
            stringToSign += headers["content-md5"]
        stringToSign += '\n'
        if "content-type" in headers:
            stringToSign += headers["content-type"]
        stringToSign += '\n'
        stringToSign += self.canonicalize_xiaomi_headers(headers) + canonicalizeResource
        key = str(self.credential.secretKey).encode("utf-8")
        msg = stringToSign.encode("utf-8")
        mac = hmac.new(key, msg, hashlib.sha1)
        returnStr = str(base64.b64encode(mac.digest()).decode("utf-8"))
        return returnStr

    def canonicalize_xiaomi_headers(self, headers=None):
        if not headers:
            return ""
        else:
            canonicalizedKeys = list()
            canonicalizedHeaders = dict()
            for (k, v) in headers.items():
                lowerKey = str(k).lower()
                if "x-xiaomi-" in lowerKey:
                    canonicalizedKeys.append(lowerKey)
                    canonicalizedHeaders[lowerKey] = v + '\n'
            canonicalizedKeys.sort()
            result = "\n"
            for k in canonicalizedKeys:
                result += k
                result += ':'
                result += canonicalizedHeaders[k]
            return result

    def canonicalize_resource(self, uri=None):
        subResource = ["acl", "quota", "uploads", "partNumber", "uploadId", "storageAccessToken", "metadata"]
        parsedUrl = http_client.urlsplit(url=uri)
        result = parsedUrl.path
        queryArgs = parsedUrl.query
        canonicalizeQuery = []
        for k in queryArgs:
            if k in subResource:
                canonicalizeQuery.append(k)
        if not len(canonicalizeQuery) == 0:
            i = 0
            canonicalizeQuery.sort()
            for k in canonicalizeQuery:
                if i == 0:
                    result += '?'
                else:
                    result += '&'
                values = queryArgs[k]
                if len(values) == 1 and values[0] == "":
                    result += k
                else:
                    result += k
                    result += '='
                    result += values[len(values) - 1]
                i += 1

        return result

    def isOpen(self):
        return self.__http is not None

    def open(self):
        if self.scheme == 'http':
            self.__http = http_client.HTTPConnection(self.get_addr_by_host(self.host), self.port,
                                                     timeout=self.__timeout)
        elif self.scheme == 'https':
            self.__http = http_client.HTTPSConnection(self.get_addr_by_host(self.host), self.port,
                                                      key_file=self.keyfile,
                                                      cert_file=self.certfile,
                                                      timeout=self.__timeout,
                                                      context=self.context)
        if self.using_proxy():
            self.__http.set_tunnel(self.get_addr_by_host(self.realhost), self.realport,
                                   {"Proxy-Authorization": self.proxy_auth})

    def close(self):
        self.__http.close()
        self.__http = None
        self.__http_response = None

    def read(self, sz):
        return self.__http_response.read(sz)

    def write(self, buf):
        self.__wbuf.write(buf)

    def flush(self):
        if self.isOpen():
            self.close()
        self.open()

        # Pull data out of buffer
        data = self.__wbuf.getvalue()
        self.__wbuf = BytesIO()

        # HTTP request
        requestId = self.generate_random_id(self._REQUEST_ID_LENGTH)
        sb = str(self.path)
        sb += "?id="
        sb += requestId
        if self._queryString:
            sb += "&"
            sb += self._queryString

        if self.using_proxy() and self.scheme == "http":
            # need full URL of real host for HTTP proxy here (HTTPS uses CONNECT tunnel)
            self.__http.putrequest('POST', "http://%s:%s%s" %
                                   (self.realhost, self.realport, sb))
        else:
            self.__http.putrequest('POST', sb)

        # Write headers
        self.__http.putheader('Content-Type', 'application/x-thrift-compact')
        self._headers['Content-Type'.lower()] = 'application/x-thrift-compact'
        self.__http.putheader('Content-Length', str(len(data)))
        self._headers['Content-Length'] = str(len(data))
        self.__http.putheader('Accept', 'application/x-thrift-compact')
        self._headers['Accept'.lower()] = 'application/x-thrift-compact'
        if self.using_proxy() and self.scheme == "http" and self.proxy_auth is not None:
            self.__http.putheader("Proxy-Authorization", self.proxy_auth)
            self._headers["Proxy-Authorization".lower()] = self.proxy_auth

        if not self.__custom_headers or 'User-Agent' not in self.__custom_headers:
            user_agent = 'Python/THttpClient'
            script = os.path.basename(sys.argv[0])
            if script:
                user_agent = '%s (%s)' % (user_agent, urllib.parse.quote(script))
            self.__http.putheader('User-Agent', user_agent)
            self._headers['User-Agent'.lower()] = user_agent

        if self.__custom_headers:
            for key, val in six.iteritems(self.__custom_headers):
                self.__http.putheader(key, val)
                self._headers[key] = val

        self.set_authentication_headers(data)

        self.__http.endheaders()

        # Write payload
        self.__http.send(data)

        # Get reply to flush the request
        self.__http_response = self.__http.getresponse()
        self.code = self.__http_response.status
        response = self.__http_response
        if not self.code == 200:
            isTalosTransportError = True
            headers = response.headers._headers
            for i in headers:
                if i[0] == 'Content-Type':
                    isTalosTransportError = False
                    if not re.match('application/x-thrift', i[1]):
                        isTalosTransportError = True

            if isTalosTransportError:
                self.adjustClock(response, self.code)
                raise TalosTransportError(self.code, response.reason,
                                          current_time_mills())

    # Adjust local clock when clock skew error received from server.The client clock need to be
    # roughly synchronized with server clock to make signature secure
    # and reduce the chance of replay attacks.
    # @ param response server response
    # @ param httpStatusCode status code
    # @ return if clock is adjusted
    def adjustClock(self, response, httpStatusCode):
        if httpStatusCode == HttpStatusCode.CLOCK_TOO_SKEWED:
            headers = response.heasers(constants.HK_TIMESTAMP)
            for key, hv in headers.items():
                serverTime = int(hv)
                min = 60 * 60 * 24 * 365 * (2010 - 1970)
                max = 60 * 60 * 24 * 365 * (2030 - 1970)
            if serverTime > min and serverTime < max:
                self.logger.debug("Adjusting client time from {} to {}" +
                                  str(self._clockOffset) + " serverTime: " + str(
                    serverTime))
                self._clockOffset = serverTime
                return True
        return False

    def generate_random_id(self, length=None):
        return str(uuid.uuid4())[0:length]

    def set_query_string(self, queryString=None):
        self._queryString = queryString

    def set_clock_offset(self, clockOffset=None):
        self._clockOffset = clockOffset

    def set_sid(self, sid=None):
        self._sid = sid


    def is_ip_address(self, host=None):
        try:
            IPy.IP(host)
            return True
        except Exception as e:
            return False


    # for dns cache
    def get_addr_by_host(self, host=None):
        if not self._supportDnsResolver or self.is_ip_address(host):
            return host

        ipList = []
        try:
            A = dns.resolver.query(host)
            if len(A.response.answer) > 0:
                for items in A.response.answer:
                    for item in items:
                        ipList.append(item)
                return str(random.choice(ipList))
        except Exception as e:
            self.logger.info("dns resolve error for host: "
                             + host + str(traceback.format_exc()))
        return host

