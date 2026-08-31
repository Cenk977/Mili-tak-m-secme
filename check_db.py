#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/selection.db')
cursor = conn.cursor()

# Check fed_results
cursor.execute("SELECT COUNT(*) FROM fed_results")
fed_results_count = cursor.fetchone()[0]
print(f"fed_results: {fed_results_count} records")

# Check fed_athlete_best
cursor.execute("SELECT COUNT(*) FROM fed_athlete_best")
fed_athlete_best_count = cursor.fetchone()[0]
print(f"fed_athlete_best: {fed_athlete_best_count} records")

# Sample from fed_athlete_best
cursor.execute("SELECT athlete_name, birth_year, gender, best_points, best_leg FROM fed_athlete_best LIMIT 5")
print("\nSample from fed_athlete_best:")
for row in cursor.fetchall():
    print(f"  {row}")

# Check 2014 M athletes
cursor.execute("SELECT athlete_name, birth_year, gender, best_points FROM fed_athlete_best WHERE birth_year=2014 AND gender='M' LIMIT 5")
print("\n2014 Male athletes:")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
