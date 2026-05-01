# proxy11

[![PyPI](https://img.shields.io/pypi/v/proxy11.svg)](https://pypi.org/project/proxy11/)
[![Python](https://img.shields.io/pypi/pyversions/proxy11.svg)](https://pypi.org/project/proxy11/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Official Python client for the [Proxy11](https://proxy11.com) proxy API.

Use it to fetch fresh proxy lists, filter by country or anonymity type, rotate through proxies, and export simple `ip:port` files.

## Install

```bash
pip install proxy11
```

## Quick Start

```python
from proxy11 import ProxyClient

client = ProxyClient(api_key="YOUR_API_KEY")

proxies = client.get(limit=50, country="us")
proxy = client.random(proxy_type="anonymous")
proxy_list = client.as_list(limit=100)
```

## Examples

### Get Proxies

```python
proxies = client.get(limit=50, country="us", proxy_type="anonymous", speed=1.0)
```

### Get `ip:port` List

```python
proxies = client.as_list(limit=50)
# ["103.152.112.166:8080", "45.77.56.114:4145"]
```

### Random Proxy

```python
proxy = client.random(country="us")
proxy_details = client.random_proxy()
```

### Save to File

```python
count = client.save("proxies.txt", country="us")
print(f"saved {count} proxies")
```

## Rotator

```python
rotator = client.rotator(country="us", proxy_type="anonymous", auto_refresh=True, refresh_after=50)

for _ in range(100):
    proxy = rotator.next()
    print(proxy)
    # if proxy fails:
    # rotator.mark_dead(proxy)
```

## Auto-Rotating Requests Session

```python
session = client.session(country="us", proxy_type="anonymous")

resp = session.get("https://httpbin.org/ip", timeout=15)
print(resp.json())
```

## Error Handling

```python
from proxy11 import APIError, NoProxiesError, ProxyClient

client = ProxyClient("YOUR_API_KEY")

try:
    proxy = client.random(country="us")
except NoProxiesError:
    print("No proxies matched the filters")
except APIError as exc:
    print(f"Proxy11 API error: {exc}")
```

## API

| Method | Description |
|--------|-------------|
| `get(**filters)` | Return proxy rows as dictionaries |
| `as_list(**filters)` | Return proxies as `ip:port` strings |
| `random(**filters)` | Return one random `ip:port` proxy |
| `random_proxy(**filters)` | Return one random proxy dictionary |
| `save(path, **filters)` | Save `ip:port` proxies to a file |
| `rotator(**filters)` | Create a proxy rotator |
| `session(**filters)` | Create a `requests.Session` with rotating proxies |

## Filters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max proxies to return, capped by your plan |
| `country` | string | Country name or two-letter country code |
| `port` | int | Proxy port |
| `speed` | float | Max response time in seconds |
| `proxy_type` | string | `anonymous` or `transparent` |

## Links

- Website: [proxy11.com](https://proxy11.com)
- API docs: [proxy11.com/apidoc](https://proxy11.com/apidoc)
- SDK page: [proxy11.com/sdk](https://proxy11.com/sdk)

## License

MIT
