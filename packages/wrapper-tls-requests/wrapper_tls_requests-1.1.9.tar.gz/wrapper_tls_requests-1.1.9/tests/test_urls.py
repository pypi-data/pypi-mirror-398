from urllib.parse import unquote

from pytest_httpserver import HTTPServer

import tls_requests


def request_hook(_request, response):
    response.headers['x-path'] = _request.full_path
    return response


def test_request_params(httpserver: HTTPServer):
    params = {"a": "1", "b": "2"}
    httpserver.expect_request("/params").with_post_hook(request_hook).respond_with_data(b"OK")
    response = tls_requests.get(httpserver.url_for("/params"), params=params)
    assert response.status_code == 200
    assert unquote(str(response.url)).endswith(unquote(response.headers["x-path"]))


def test_request_multi_params(httpserver: HTTPServer):
    params = {"a": ["1", "2", "3"]}
    httpserver.expect_request("/params").with_post_hook(request_hook).respond_with_data(b"OK")
    response = tls_requests.get(httpserver.url_for("/params"), params=params)
    assert response.status_code == 200
    assert unquote(str(response.url)).endswith(unquote(response.headers["x-path"]))
