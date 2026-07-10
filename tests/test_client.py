import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from proxy11 import APIError, NoProxiesError, Proxy11Error, ProxyClient


class FakeClient(ProxyClient):
    def __init__(self):
        self.calls = []

    def as_list(self, **kwargs):
        self.calls.append(kwargs)
        return ["1.1.1.1:80", "2.2.2.2:8080"]


def test_rotator_uses_default_limit_when_not_provided():
    client = FakeClient()

    proxy = client.rotator(country="us").next()

    assert proxy in {"1.1.1.1:80", "2.2.2.2:8080"}
    assert client.calls == [{"country": "us", "limit": 200}]


def test_rotator_preserves_user_limit():
    client = FakeClient()

    proxy = client.rotator(limit=10, country="us").next()

    assert proxy in {"1.1.1.1:80", "2.2.2.2:8080"}
    assert client.calls == [{"limit": 10, "country": "us"}]


def test_rotator_raises_when_no_proxies():
    class EmptyClient(FakeClient):
        def as_list(self, **kwargs):
            self.calls.append(kwargs)
            return []

    with pytest.raises(NoProxiesError, match="No proxies available"):
        EmptyClient().rotator(limit=10).next()


def test_rotator_raises_when_refresh_returns_no_proxies():
    class RefreshEmptyClient(FakeClient):
        def as_list(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return ["1.1.1.1:80"]
            return []

    rotator = RefreshEmptyClient().rotator(limit=10, refresh_after=1)

    assert rotator.next() == "1.1.1.1:80"
    with pytest.raises(NoProxiesError, match="No proxies available"):
        rotator.next()


def test_get_raises_api_error_for_error_payload():
    class Response:
        status_code = 200

        def json(self):
            return {"error": True, "msg": "bad key"}

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    client = ProxyClient("key")
    client._session = Session()

    with pytest.raises(APIError, match="bad key"):
        client.get()


def test_client_errors_still_behave_like_value_error():
    assert issubclass(APIError, Proxy11Error)
    assert issubclass(NoProxiesError, Proxy11Error)
    assert issubclass(Proxy11Error, ValueError)


def test_rotate_sends_strategy_and_filters_to_rotate_endpoint():
    captured = {}

    class Response:
        status_code = 200

        def json(self):
            return {"ip": "1.1.1.1", "port": "80", "strategy": "sticky"}

    class Session:
        def get(self, url, params=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            return Response()

    client = ProxyClient("key")
    client._session = Session()

    data = client.rotate(strategy="sticky", session="s1", sticky_seconds=120,
                         country="us", proxy_type="anonymous")

    assert captured["url"].endswith("/api/rotate")
    assert captured["params"]["key"] == "key"
    assert captured["params"]["strategy"] == "sticky"
    assert captured["params"]["session"] == "s1"
    assert captured["params"]["sticky_seconds"] == 120
    assert captured["params"]["country"] == "us"
    assert captured["params"]["type"] == "anonymous"
    assert data["ip"] == "1.1.1.1"


def test_rotate_txt_returns_bare_ip_port():
    class Response:
        status_code = 200
        text = "1.1.1.1:80\n"

        def json(self):
            raise ValueError("not json")

    captured = {}

    class Session:
        def get(self, url, params=None, timeout=None):
            captured["url"] = url
            return Response()

    client = ProxyClient("key")
    client._session = Session()

    assert client.rotate(fmt="txt") == "1.1.1.1:80"
    assert captured["url"].endswith("/api/rotate.txt")


def test_rotate_raises_no_proxies_on_404():
    class Response:
        status_code = 404
        reason = "Not Found"

        def json(self):
            return {"error": True, "msg": "no proxies match"}

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    client = ProxyClient("key")
    client._session = Session()

    with pytest.raises(NoProxiesError, match="No proxies available"):
        client.rotate()


def test_rotate_raises_api_error_on_bad_request():
    class Response:
        status_code = 400
        reason = "Bad Request"

        def json(self):
            return {"error": True, "msg": "strategy must be random or sticky"}

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    client = ProxyClient("key")
    client._session = Session()

    with pytest.raises(APIError, match="strategy must be random or sticky"):
        client.rotate(strategy="bad")
