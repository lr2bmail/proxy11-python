from proxy11 import ProxyClient


client = ProxyClient(api_key="YOUR_API_KEY")
count = client.save("proxies.txt", limit=100, country="us")

print(f"saved {count} proxies")
