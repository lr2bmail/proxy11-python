from proxy11 import ProxyClient


client = ProxyClient(api_key="YOUR_API_KEY")

for proxy in client.get(limit=10, country="us"):
    print(proxy)
