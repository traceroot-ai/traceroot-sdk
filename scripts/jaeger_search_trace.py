import time
from pprint import pprint

import requests

minutes = 10

# Current time in microseconds
end_time = int(time.time() * 1_000_000)

# 30 minutes ago in microseconds
start_time = end_time - (minutes * 60 * 1_000_000)

params = {
    "service": "sdk-example-service",
    "start": start_time,
    "end": end_time,
    "limit": 20
}

response = requests.get("http://localhost:16686/api/traces", params=params)

if response.ok:
    traces = response.json()["data"]
    pprint(traces)
else:
    print(f"Error: {response.status_code} - {response.text}")
