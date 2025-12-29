import tls_requests


def test_http_proxy():
    proxy = tls_requests.Proxy("http://localhost:8080")
    assert proxy.scheme == "http"
    assert proxy.host == "localhost"
    assert proxy.port == '8080'
    assert proxy.url == "http://localhost:8080"


def test_https_proxy():
    proxy = tls_requests.Proxy("https://localhost:8080")
    assert proxy.scheme == "https"
    assert proxy.host == "localhost"
    assert proxy.port == '8080'
    assert proxy.url == "https://localhost:8080"


def test_socks5_proxy():
    proxy = tls_requests.Proxy("socks5://localhost:8080")
    assert proxy.scheme == "socks5"
    assert proxy.host == "localhost"
    assert proxy.port == '8080'
    assert proxy.url == "socks5://localhost:8080"


def test_proxy_with_params():
    proxy = tls_requests.Proxy("http://localhost:8080?a=b", params={"foo": "bar"})
    assert proxy.scheme == "http"
    assert proxy.host == "localhost"
    assert proxy.port == '8080'
    assert proxy.url == "http://localhost:8080"


def test_auth_proxy():
    proxy = tls_requests.Proxy("http://username:password@localhost:8080")
    assert proxy.scheme == "http"
    assert proxy.host == "localhost"
    assert proxy.port == '8080'
    assert proxy.auth == ("username", "password")
    assert proxy.url == "http://username:password@localhost:8080"


def test_unsupported_proxy_scheme():
    try:
        _ = tls_requests.Proxy("unknown://localhost:8080")
    except Exception as e:
        assert isinstance(e, tls_requests.exceptions.ProxyError)
