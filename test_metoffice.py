#!/usr/bin/env python3
"""
Test Met Office DataHub API map-images endpoints using key from config.json.
"""

import json
import ssl
import urllib.request

with open("config.json", "r") as f:
    cfg = json.load(f)

api_key = cfg.get("met_office_api_key", "")

print(f"API Key present: {bool(api_key)}, Length: {len(api_key)}")

# Met Office API endpoints to test
endpoints = [
    "https://api-metoffice.apiconnect.ibmcloud.com/metoffice/production/1.0.0/map-images/capabilities",
    "https://data.hub.metoffice.gov.uk/map-images/1.0.0/capabilities"
]

ctx = ssl._create_unverified_context()

for url in endpoints:
    print(f"\nTesting endpoint: {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "apikey": api_key,
                "accept": "application/json"
            }
        )
        res = urllib.request.urlopen(req, context=ctx, timeout=8)
        data = res.read().decode("utf-8")
        print("SUCCESS! Response status:", res.status)
        print("Response snippet:", data[:400])
        break
    except Exception as e:
        print(f"Failed: {e}")
