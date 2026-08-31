#!/usr/bin/env python3
import sqlite3
from collections import defaultdict

conn = sqlite3.connect('data/selection.db')
cursor = conn.cursor()

# Get distinct birth years
cursor.execute("SELECT DISTINCT birth_year FROM fed_athlete_best ORDER BY birth_year DESC")
years = cursor.fetchall()
print("Birth years in database:")
for (year,) in years:
    print(f"  {year}")

# Check 2014 M
cursor.execute("SELECT COUNT(*) FROM fed_athlete_best WHERE birth_year=2014 AND gender='M'")
count_2014_m = cursor.fetchone()[0]
print(f"\n2014 Male records in fed_athlete_best: {count_2014_m}")

# Check how many unique athletes
cursor.execute("SELECT COUNT(DISTINCT athlete_name) FROM fed_athlete_best WHERE birth_year=2011 AND gender='M'")
unique_athletes_2011 = cursor.fetchone()[0]
print(f"2011 Male unique athletes: {unique_athletes_2011}")

# Check rows per athlete for 2011 M
cursor.execute("SELECT athlete_name, COUNT(*) as cnt FROM fed_athlete_best WHERE birth_year=2011 AND gender='M' GROUP BY athlete_name LIMIT 5")
print("\nRows per athlete (2011 M, first 5):")
for name, cnt in cursor.fetchall():
    print(f"  {name}: {cnt} rows")

conn.close()
