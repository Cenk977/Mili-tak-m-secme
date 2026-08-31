#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('data/selection.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Test the query directly
query = """
    SELECT
        athlete_name, birth_year, gender, region, city, club,
        MAX(best_points) as best_points,
        best_leg
    FROM fed_athlete_best
    WHERE birth_year=2011 AND gender='M'
    GROUP BY athlete_name, birth_year, gender
    ORDER BY best_points DESC
    LIMIT 5
"""

cursor.execute(query)
rows = cursor.fetchall()

print("Direct SQL query result:")
for row in rows:
    athlete = dict(row)
    print(f"  {athlete}")

conn.close()
