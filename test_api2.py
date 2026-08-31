#!/usr/bin/env python3
import requests
import json

# Test with 2011 (which we have data for)
url = 'http://localhost:8765/api/ranking?leg=combined&birth_year=2011&gender=M'
response = requests.get(url)
athletes = response.json()

print(f'Total: {len(athletes)} athletes (2011, Male)')
print()
print('First 10 athletes:')
for i, athlete in enumerate(athletes[:10], 1):
    print(f"{i}. {athlete.get('athlete_name')} - Points: {athlete.get('best_points')} - Selection: {athlete.get('selection_type')}")

# Test with region filter
print('\n--- With Region 1 Filter ---')
url = 'http://localhost:8765/api/ranking?leg=combined&birth_year=2011&gender=M&region=1'
response = requests.get(url)
athletes = response.json()
print(f'Total: {len(athletes)} athletes (2011, Male, Region 1)')
for i, athlete in enumerate(athletes[:5], 1):
    print(f"{i}. {athlete.get('athlete_name')} - Points: {athlete.get('best_points')} - Selection: {athlete.get('selection_type')}")
