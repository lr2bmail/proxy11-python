import random
import requests


BASE_URL = "https://proxy11.com/api/proxy.json"


class Proxy11Error(ValueError):
    """Base exception for Proxy11 client errors."""


class APIError(Proxy11Error):
    """Raised when the Proxy11 API returns an error response."""


class NoProxiesError(Proxy11Error):
    """Raised when no proxies are available for the requested filters."""


class ProxyClient:
    """Lightweight client for the Proxy11 API."""

    def __init__(self, api_key, base_url=None, timeout=10):
        self.api_key = api_key
        self.base_url = base_url or BASE_URL
        self.timeout = timeout
        self._session = requests.Session()

    def get(self, limit=None, country=None, proxy_type=None, speed=None, port=None):
        """Fetch proxies from the API. Returns list of dicts."""
        params = {"key": self.api_key}
        if limit is not None:
            params["limit"] = int(limit)
        if country is not None:
            params["country"] = country
        if proxy_type is not None:
            params["type"] = proxy_type
        if speed is not None:
            params["speed"] = float(speed)
        if port is not None:
            params["port"] = int(port)

        resp = self._session.get(self.base_url, params=params, timeout=self.timeout)

        if resp.status_code >= 400:
            try:
                body = resp.json()
                msg = body.get("msg", resp.reason)
            except Exception:
                msg = resp.reason
            raise APIError("API error {0}: {1}".format(resp.status_code, msg))

        try:
            data = resp.json()
        except ValueError as exc:
            raise APIError("API returned invalid JSON") from exc
        if isinstance(data, dict) and data.get("error"):
            raise APIError(data.get("msg", "API error"))
        if not isinstance(data, list):
            raise APIError("API returned unexpected data")
        return data

    def as_list(self, **kwargs):
        """Return proxies as a list of 'ip:port' strings."""
        results = []
        for p in self.get(**kwargs):
            try:
                results.append("{0}:{1}".format(p["ip"], p["port"]))
            except (KeyError, TypeError):
                continue
        return results

    def random(self, **kwargs):
        """Return one random proxy as 'ip:port'. Fetches up to 100 for pool size."""
        kwargs.setdefault("limit", 100)
        proxies = self.as_list(**kwargs)
        if not proxies:
            raise NoProxiesError("No proxies available")
        return random.choice(proxies)

    def random_proxy(self, **kwargs):
        """Return one random proxy as a dict with full details."""
        kwargs.setdefault("limit", 100)
        proxies = self.get(**kwargs)
        if not proxies:
            raise NoProxiesError("No proxies available")
        return random.choice(proxies)

    def save(self, path, **kwargs):
        """Save proxies to a text file, one ip:port per line."""
        proxies = self.as_list(**kwargs)
        if not proxies:
            return 0
        with open(path, "w") as f:
            f.write("\n".join(proxies) + "\n")
        return len(proxies)

    def rotator(self, on_fail=None, auto_refresh=False, refresh_after=10, **kwargs):
        """Return a ProxyRotator that cycles through proxies.

        Args:
            on_fail: callable(proxies) called when all proxies are exhausted.
            auto_refresh: if True, re-fetches from API when pool is empty.
            refresh_after: rotate this many times before re-fetching (0 = never).
            **kwargs: filters passed to get() (country, proxy_type, etc).
        """
        return ProxyRotator(self, on_fail=on_fail, auto_refresh=auto_refresh,
                            refresh_after=refresh_after, **kwargs)

    def session(self, on_fail=None, **kwargs):
        """Return a requests.Session that auto-rotates proxy on each request.

        Args:
            on_fail: callable(proxy_str) called when a request fails.
            **kwargs: filters passed to get() (country, proxy_type, etc).
        """
        rotator = self.rotator(on_fail=on_fail, auto_refresh=True, **kwargs)
        return _ProxySession(rotator)


class ProxyRotator:
    """Cycles through a pool of proxies, optionally auto-refreshing."""

    def __init__(self, client, on_fail=None, auto_refresh=False, refresh_after=0, **kwargs):
        self.client = client
        self.on_fail = on_fail
        self.auto_refresh = auto_refresh
        self.refresh_after = refresh_after
        self.kwargs = kwargs
        self._pool = []
        self._index = 0
        self._count = 0
        self._refresh()

    def _refresh(self):
        """Fetch a fresh batch of proxies."""
        params = dict(self.kwargs)
        params.setdefault("limit", 200)
        self._pool = self.client.as_list(**params)
        random.shuffle(self._pool)
        self._index = 0
        self._count = 0

    def next(self):
        """Return the next proxy as 'ip:port'. Raises NoProxiesError if pool is empty."""
        if not self._pool:
            if self.auto_refresh:
                self._refresh()
            if not self._pool:
                raise NoProxiesError("No proxies available")

        # refresh after N rotations to keep pool fresh
        if self.refresh_after and self._count >= self.refresh_after:
            self._refresh()

        proxy = self._pool[self._index % len(self._pool)]
        self._index += 1
        self._count += 1
        return proxy

    def mark_dead(self, proxy):
        """Remove a proxy from the pool and call on_fail if set."""
        try:
            self._pool.remove(proxy)
        except ValueError:
            pass
        if self.on_fail:
            self.on_fail(proxy)

    @property
    def remaining(self):
        return len(self._pool)


class _ProxySession(requests.Session):
    """requests.Session that sets a new proxy before each request."""

    def __init__(self, rotator):
        super().__init__()
        self._rotator = rotator
        self._current_proxy = None

    def request(self, method, url, **kwargs):
        proxy = self._rotator.next()
        self._current_proxy = proxy
        kwargs.setdefault("proxies", {
            "http": "http://{0}".format(proxy),
            "https": "http://{0}".format(proxy),
        })
        try:
            return super().request(method, url, **kwargs)
        except requests.exceptions.ProxyError:
            self._rotator.mark_dead(proxy)
            raise
