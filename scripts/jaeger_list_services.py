import requests

lookback_seconds = 1 * 60 * 60  # 1 hour

params = {"lookback": f"{lookback_seconds}s"}

response = requests.get("http://localhost:16686/api/services", params=params)

if response.ok:
    services = response.json()["data"]
    print("Available services:")
    for service in services:
        print(f" - {service}")
else:
    print(f"Error: {response.status_code} - {response.text}")
