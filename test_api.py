#!/usr/bin/env python3
import requests
import json

url = 'http://localhost:8765/api/ranking?leg=combined&birth_year=2014&gender=M'
response = requests.get(url)
athletes = response.json()

print(f'Total: {len(athletes)} athletes')
print()
print('First 10 athletes:')
for athlete in athletes[:10]:
    print(f"  {athlete.get('athlete_name')} ({athlete.get('birth_year')}) - {athlete.get('selection_type')} - Points: {athlete.get('best_points')}")
