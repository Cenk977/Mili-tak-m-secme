# Task 5: Delete Race Leg Endpoint

## Context
This task adds the ability to delete all results for a specific race leg (Antalya or Edirne) from the database, triggering a re-computation of combined rankings.

## Requirements

**Files:**
- Modify: `panel/serve.py:650-680` (add delete handler)
- Test: Manual API calls or curl

**Interfaces:**
- Consumes: Existing database functions `get_fed_results()`, `clear_fed_tables()`
- Produces: `POST /api/delete-leg` endpoint accepting `{"leg": "antalya"|"edirne"}`

**Implementation Steps:**

### Step 1: Understand current database structure
Read `database/db.py` to confirm:
- `fed_results` table has `race_leg` column with values 'antalya', 'edirne'
- `fed_athlete_best` table has `best_leg` column
- Both tables support deletion by leg

### Step 2: Add delete handler to serve.py
Modify `do_POST()` method to add route:
```python
def do_POST(self):
    """Handle POST requests."""
    if self.path == '/upload':
        self.handle_upload()
    elif self.path == '/api/delete-leg':
        self.handle_delete_leg()  # NEW
    elif self.path == '/clear':
        self.handle_clear()
    else:
        self.send_error(404, "Not found")
```

### Step 3: Implement delete handler
Add method to `DashboardHandler` class:
```python
def handle_delete_leg(self):
    """Delete all results for a specific race leg."""
    try:
        # Read JSON body
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_error(400, "Empty body")
            return
        
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)
        leg = data.get('leg', '').lower()
        
        if leg not in ['antalya', 'edirne']:
            self.send_error(400, "Invalid leg. Must be 'antalya' or 'edirne'")
            return
        
        # Delete from both tables
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM fed_results WHERE race_leg = ?", (leg,))
        cursor.execute("DELETE FROM fed_athlete_best WHERE best_leg = ?", (leg,))
        
        deleted_results = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted {deleted_results} results for leg '{leg}'")
        
        # Send success response
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = {
            "status": "success",
            "message": f"Deleted all results for {leg}",
            "deleted_count": deleted_results
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"Error deleting leg: {e}", exc_info=True)
        self.send_error(500, str(e))
```

### Step 4: Test with curl
```bash
curl -X POST http://localhost:8765/api/delete-leg \
  -H "Content-Type: application/json" \
  -d '{"leg": "antalya"}'
```
Expected: `{"status": "success", "message": "Deleted all results for antalya", "deleted_count": 2888}`

### Step 5: Test with invalid leg
```bash
curl -X POST http://localhost:8765/api/delete-leg \
  -H "Content-Type: application/json" \
  -d '{"leg": "invalid"}'
```
Expected: 400 error "Invalid leg"

## Global Constraints
- UTF-8 encoding throughout
- Responses use `ensure_ascii=False` for JSON
- Port: localhost:8765
- Database: data/selection.db

## Deliverables
- ✅ `POST /api/delete-leg` endpoint working
- ✅ Tests passing (delete valid leg, reject invalid leg)
- ✅ Git commit with implementation

## Report File
Write detailed report to: `C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme\.superpowers\sdd\task4-9-completion\task-5-report.md`

Include:
- Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED
- Test results (curl commands run, responses received)
- Commits made (git hash range)
- Any issues or concerns
