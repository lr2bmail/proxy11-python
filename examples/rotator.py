from proxy11 import ProxyClient


client = ProxyClient(api_key="YOUR_API_KEY")
rotator = client.rotator(country="us", proxy_type="anonymous", auto_refresh=True)

for _ in range(10):
    print(rotator.next())
