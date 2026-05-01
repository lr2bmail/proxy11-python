# proxy11

Lightweight Python client for the [Proxy11](https://proxy11.com) free proxy API.

## Install

```bash
pip install proxy11
```

## Quick Start

```python
from proxy11 import ProxyClient

client = ProxyClient(api_key="YOUR_API_KEY")
```

`Proxy11Error`, `APIError`, and `NoProxiesError` are exported if you want to catch client-specific errors.

### Get proxies

```python
# all proxies as dicts
proxies = client.get()

# with filters
proxies = client.get(limit=50, country="us", proxy_type="anonymous", speed=1.0)
```

### Get as ip:port list

```python
proxies = client.as_list()
# ["103.152.112.166:8080", "45.77.56.114:4145", ...]
```

### Random proxy

```python
# one random ip:port string
proxy = client.random()
# "103.152.112.166:8080"

# random with filters
proxy = client.random(country="us", proxy_type="anonymous")

# random with full details
proxy = client.random_proxy()
# {"ip": "103.152.112.166", "port": "8080", "country": "Indonesia", ...}
```

### Save to file

```python
count = client.save("proxies.txt", country="us")
print(f"saved {count} proxies")
```

## Rotator

Cycle through proxies with auto-refresh and dead-proxy removal.

```python
rotator = client.rotator(country="us", proxy_type="anonymous",
                         auto_refresh=True, refresh_after=50)

for _ in range(100):
    proxy = rotator.next()
    print(proxy)
    # if proxy fails:
    # rotator.mark_dead(proxy)

print(f"{rotator.remaining} proxies left in pool")
```

**Options:**

| Option           | Default | Description                                           |
|------------------|---------|-------------------------------------------------------|
| `auto_refresh`   | `False` | Re-fetch from API when pool is empty                  |
| `refresh_after`  | `0`     | Re-fetch after N rotations (0 = never)                |
| `on_fail`        | `None`  | Callback `fn(proxy_str)` called by `mark_dead()`      |

## Session (auto-rotating proxy)

Get a `requests.Session` that uses a different proxy on every request. Dead proxies are automatically removed.

```python
session = client.session(country="us", proxy_type="anonymous")

# each request goes through a different proxy
resp = session.get("https://httpbin.org/ip")
print(resp.json())

resp = session.get("https://httpbin.org/headers")
print(resp.json())
```

Pass an `on_fail` callback to log dead proxies:

```python
session = client.session(on_fail=lambda p: print(f"dead: {p}"))
```

## Parameters

| Parameter    | Type   | Description                                      |
|--------------|--------|--------------------------------------------------|
| `limit`      | int    | Max proxies to return (free: 50, ultimate: 5000) |
| `country`    | string | Filter by country name or code                   |
| `port`       | int    | Filter by port number                            |
| `speed`      | float  | Max response time in seconds                     |
| `proxy_type` | string | `anonymous` or `transparent`                     |

## API Key

Get a free API key at [proxy11.com](https://proxy11.com/newaccount).

- **Free plan**: 50 proxies per request
- **Ultimate plan**: 5,000 proxies per request — [from $12](https://proxy11.com/pricing)

## License

MIT
