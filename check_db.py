import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

count_results = conn.execute("SELECT COUNT(*) as cnt FROM fed_results").fetchone()['cnt']
print(f'fed_results rows: {count_results}')

count_best = conn.execute("SELECT COUNT(*) as cnt FROM fed_athlete_best").fetchone()['cnt']
print(f'fed_athlete_best rows: {count_best}')

conn.close()
