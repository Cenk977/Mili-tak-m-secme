#!/usr/bin/env python3
import requests
import json

url = 'http://localhost:8765/api/ranking?leg=combined&birth_year=2011&gender=M'
response = requests.get(url)

print("Raw response status:", response.status_code)
print("Response text (first 500 chars):")
print(response.text[:500])

print("\nParsed JSON (first 3 athletes):")
athletes = response.json()
for athlete in athletes[:3]:
    print(f"  Type: {type(athlete)}")
    print(f"  Keys: {athlete.keys() if isinstance(athlete, dict) else 'N/A'}")
    print(f"  Content: {athlete}")
    print()
