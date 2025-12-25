import base64
import contextlib
import http.client as httplib
import json
import urllib.parse as urlparse
import ssl
from requests_toolbelt.utils import dump

from requests.auth import HTTPBasicAuth


class ApiHttpClientException(Exception):
    def __init__(self, **kwargs):
        response = kwargs.pop('response')
        content = kwargs.pop('content')
        self.message = 'Error on HttpClient. Response Status: {}, Content: {}' \
            .format(response.status, content)


class ApiClientRequest(object):

    def __init__(self, url, body=None, json_request=True, json_response=True ):
        self.url = url
        self.body = body
        self.json_request = json_request
        self.json_response = json_response


class ApiClientResponse(object):
    def __init__(self, request, response):
        """
        :type request: ApiClientRequest
        """
        self.response = response
        self.content = response.read()
        self.request = request

    def get_content(self):
        if 200 <= self.response.status < 300:
            if self.request.json_response:
                return json.loads(self.content)
            else:
                return self.content


class ApiHttpClientBase(object):
    def __init__(self, **kwargs):
        self.base_url = kwargs.pop('base_url')
        self.username = kwargs.pop('username', None)
        self.password = kwargs.pop('password', None)
        self.http_debug = kwargs.pop('http_debug', False)
        self.requests_auth = HTTPBasicAuth(self.username, self.password) if self.username and self.password else None

    @contextlib.contextmanager
    def _get_client(self):
        url_parsed = urlparse.urlparse(self.base_url)

        if self.http_debug:
            old_send = httplib.HTTPConnection.send

            def new_send(self, data):
                print (data)
                return old_send(self, data)

            httplib.HTTPConnection.send = new_send

        if url_parsed.scheme == 'http':
            yield httplib.HTTPConnection(
                url_parsed.hostname,
                url_parsed.port or 80
            )
        else:
            yield httplib.HTTPSConnection(
                url_parsed.hostname,
                url_parsed.port or 443,
                context=ssl._create_unverified_context()
            )

    def _dump_response(self, response):
        if self.http_debug:
            if not response.reason:
                response.reason = ''
            data = dump.dump_response(response)
            print(data.decode('utf-8'))

    def _get_headers(self, request):
        """
        :type request: ApiClientRequest
        """
        headers = {}
        if self.username and self.password:
            headers.update({
                'Authorization': 'Basic ' + base64.b64encode(bytes("{0}:{1}".format(self.username, self.password))),
            })
        if request.json_request:
            headers.update({
                'Content-Type': 'application/json'
            })
        return headers

    def http_head(self, request):
        """
        :type request: ApiClientRequest
        """
        headers = self._get_headers(request)

        with self._get_client() as _client:
            parsed_url = urlparse.urlparse(request.url)
            url = parsed_url.path + ('?' + parsed_url.query if parsed_url.query else '')
            _client.request(
                method="HEAD", url=url, headers=headers
            )
            _response = _client.getresponse()
            return ApiClientResponse(request, _response)

    def http_get(self, request):
        """
        :type request: ApiClientRequest
        """
        headers = self._get_headers(request)

        with self._get_client() as _client:
            parsed_url = urlparse.urlparse(request.url)
            url = parsed_url.path + ('?' + parsed_url.query if parsed_url.query else '')
            _client.request(
                method="GET", url=url, headers=headers
            )
            _response = _client.getresponse()
            return ApiClientResponse(request, _response)

    def http_post(self, request):
        """
        :type request: ApiClientRequest
        """
        with self._get_client() as _client:
            body = json.dumps(request.body) if request.json_request else request.body

            parsed_url = urlparse.urlparse(request.url)
            _client.request(
                method="POST",
                url=parsed_url.path + ('?' + parsed_url.query if parsed_url.query else ''),
                body=body,
                headers=self._get_headers(request)
            )
            _response = _client.getresponse()
            return ApiClientResponse(request, _response)

    def http_put(self, request):
        """
        :type request: ApiClientRequest
        """
        with self._get_client() as _client:
            body = json.dumps(request.body) if request.json_request else request.body

            _client.request(
                method="PUT",
                url=urlparse.urlparse(request.url).path,
                body=body,
                headers=self._get_headers(request)
            )
            _response = _client.getresponse()
            return ApiClientResponse(request, _response)

    def http_patch(self, request):
        """
        :type request: ApiClientRequest
        """
        with self._get_client() as _client:
            body = json.dumps(request.body) if request.json_request else request.body

            _client.request(
                method="PATCH",
                url=urlparse.urlparse(request.url).path,
                body=body,
                headers=self._get_headers(request)
            )
            _response = _client.getresponse()
            return ApiClientResponse(request, _response)

    def http_delete(self, request):
        """
        :type request: ApiClientRequest
        """
        with self._get_client() as _client:
            _client.request(
                method="DELETE",
                url=urlparse.urlparse(request.url).path,
                headers=self._get_headers(request)
            )
            _response = _client.getresponse()
            return ApiClientResponse(request, _response)
