# Task 4: Parser Integration (`modules/lxf_parser.py`)

**Files:**
- Modify: `modules/lxf_parser.py`

**Interfaces:**
- Consumes:
  - `lookup_club(club_name: str)` from m4_mapping (Task 3)
- Produces:
  - Updated `parse_lxf_file()` signature — same return type, but athletes now have `city` and `region` fields

## Step 1: Add import and lookup call in parse_lxf_file()

At top of `modules/lxf_parser.py`, add import:

```python
from modules.m4_mapping import lookup_club
```

Find the line that creates the athlete dict (around line 56-65). Current code:

```python
athlete = {
    'athlete_id': athlete_id,
    'firstname': athlete_elem.get('firstname'),
    'lastname': athlete_elem.get('lastname'),
    'birthdate': athlete_elem.get('birthdate'),
    'gender': athlete_elem.get('gender'),
    'license': athlete_elem.get('license'),
    'club_id': None,
    'club_name': None,
}

# Get club info if available
club_elem = athlete_elem.find('.//CLUB')
if club_elem is not None:
    athlete['club_id'] = club_elem.get('clubid')
    athlete['club_name'] = club_elem.get('clubname')
```

Replace with:

```python
athlete = {
    'athlete_id': athlete_id,
    'firstname': athlete_elem.get('firstname'),
    'lastname': athlete_elem.get('lastname'),
    'birthdate': athlete_elem.get('birthdate'),
    'gender': athlete_elem.get('gender'),
    'license': athlete_elem.get('license'),
    'club_id': None,
    'club_name': None,
    'city': 'Unknown',      # ← ADD
    'region': 0,            # ← ADD
}

# Get club info if available
club_elem = athlete_elem.find('.//CLUB')
if club_elem is not None:
    athlete['club_id'] = club_elem.get('clubid')
    athlete['club_name'] = club_elem.get('clubname')
    
    # ← ADD: Look up city/region from Excel mapping
    if athlete['club_name']:
        mapping = lookup_club(athlete['club_name'])
        if mapping:
            athlete['city'] = mapping['city']
            athlete['region'] = mapping['region']
```

## Step 2: Test parser with Antalya LXF

Run:
```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
python -c "
from modules.lxf_parser import parse_lxf_file
athletes, results = parse_lxf_file('data/antalya_millitakim_secme_sonuc.lxf')
print(f'Parsed {len(athletes)} athletes')
for a in athletes[:3]:
    print(f\"  {a['firstname']} {a['lastname']}: {a['club_name']} → {a['city']} (region {a['region']})\")
"
```

Expected: 
- 2,888 results parsed
- Athletes have `city` and `region` fields populated (or 'Unknown'/0 if not in mapping)

## Step 3: Commit

```bash
git add modules/lxf_parser.py
git commit -m "feat: integrate city/region mapping into LXF parser"
```
