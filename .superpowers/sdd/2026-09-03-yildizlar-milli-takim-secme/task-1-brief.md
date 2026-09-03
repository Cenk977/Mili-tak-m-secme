# Task 1: Extend Database Schema

**Files:**
- Modify: `database/db.py` (athletes table definition + initialization)

**Interfaces:**
- Consumes: Existing `athletes` table structure
- Produces: Extended `athletes` table with 10 new boolean columns for yíldízlar selections

**Steps:**

- [ ] **Step 1: Open `database/db.py` and locate `CREATE TABLE athletes`**

Find the athletes table definition (around line 20–50). Note current columns: athlete_name, birth_year, gender, region, city, club, etc.

- [ ] **Step 2: Add 10 new columns to CREATE TABLE statement**

After existing columns, add:
```sql
selected_yildiz_multinations BOOLEAN DEFAULT 0,
coach_called_yildiz_multinations BOOLEAN DEFAULT 0,
selected_yildiz_comen_cup_aralik BOOLEAN DEFAULT 0,
selected_yildiz_comen_cup_nisan BOOLEAN DEFAULT 0,
coach_called_yildiz_comen_cup_aralik BOOLEAN DEFAULT 0,
coach_called_yildiz_comen_cup_nisan BOOLEAN DEFAULT 0,
selected_yildiz_central_europe_aralik BOOLEAN DEFAULT 0,
selected_yildiz_central_europe_nisan BOOLEAN DEFAULT 0,
coach_called_yildiz_central_europe_aralik BOOLEAN DEFAULT 0,
coach_called_yildiz_central_europe_nisan BOOLEAN DEFAULT 0
```

- [ ] **Step 3: Add migration logic (if database exists)**

In `db.py` `init_db()` function, after table creation, add ALTER TABLE statements for existing databases:
```python
try:
    cursor.execute("ALTER TABLE athletes ADD COLUMN selected_yildiz_multinations BOOLEAN DEFAULT 0")
except sqlite3.OperationalError:
    pass  # Column already exists
# ... repeat for all 10 new columns
```

- [ ] **Step 4: Update any SELECT/INSERT queries to handle new columns**

Search `db.py` for `SELECT * FROM athletes` and update column lists if needed. Update `get_athletes_by_filter()` to include new columns in returned dict.

- [ ] **Step 5: Test database initialization**

Run: `python -c "from database.db import init_db; init_db()"`

Expected: No errors; verify new columns exist with `sqlite3 database/athletes.db ".schema athletes"`

- [ ] **Step 6: Commit**

```bash
git add database/db.py
git commit -m "db: extend athletes table with 10 yildizlar selection columns"
```
