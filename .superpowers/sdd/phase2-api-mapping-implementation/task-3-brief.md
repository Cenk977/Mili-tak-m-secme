# Task 3: Mapping Module (`modules/m4_mapping.py`)

**Files:**
- Create: `modules/m4_mapping.py`
- Modify: `modules/__init__.py` (optional export)

**Interfaces:**
- Consumes:
  - `config.MAPPING_EXCEL_PATH`
  - `config.MAPPING_SHEET_NAME`
  - `config.COL_*` constants (from Task 2)
- Produces:
  - `class ClubInfo(TypedDict)` with `city`, `region`, `club_canonical`
  - `load_mapping() -> None` (idempotent, caches)
  - `lookup_club(club_name: str) -> ClubInfo | None`
  - `get_missing_clubs(athletes: List[Dict]) -> Set[str]`

## Step 1: Write mapping module

Create `modules/m4_mapping.py`:

```python
"""
m4_mapping.py — Club → City → Region lookup
Reads Excel "Kulüp Şehir Mapping.xlsx", caches in memory.
"""

from typing import TypedDict, Optional
import openpyxl
import logging

from config import (
    MAPPING_EXCEL_PATH,
    MAPPING_SHEET_NAME,
    MAPPING_DATA_START_ROW,
    COL_CLUB_ALT,
    COL_CLUB_CANONICAL,
    COL_CITY,
    COL_REGION,
)

logger = logging.getLogger(__name__)


class ClubInfo(TypedDict):
    """Club mapping info."""
    city: str
    region: int
    club_canonical: str


# Global cache
_mapping_cache: Optional[dict[str, ClubInfo]] = None


def load_mapping():
    """
    Load Excel mapping into memory cache.
    Idempotent — only loads once, subsequent calls use cache.
    """
    global _mapping_cache
    
    if _mapping_cache is not None:
        return  # Already loaded
    
    _mapping_cache = {}
    
    try:
        wb = openpyxl.load_workbook(MAPPING_EXCEL_PATH, read_only=True, data_only=True)
    except FileNotFoundError:
        logger.error(f"Mapping Excel not found: {MAPPING_EXCEL_PATH}")
        return
    
    if MAPPING_SHEET_NAME not in wb.sheetnames:
        logger.error(f"Sheet '{MAPPING_SHEET_NAME}' not found in {MAPPING_EXCEL_PATH}")
        wb.close()
        return
    
    ws = wb[MAPPING_SHEET_NAME]
    
    # Iterate rows starting from MAPPING_DATA_START_ROW
    for row_idx, row in enumerate(ws.iter_rows(min_row=MAPPING_DATA_START_ROW, values_only=True), start=MAPPING_DATA_START_ROW):
        if not row or len(row) < COL_REGION + 1:
            continue
        
        # Extract columns
        club_alt = row[COL_CLUB_ALT] if COL_CLUB_ALT < len(row) else None
        club_canonical = row[COL_CLUB_CANONICAL] if COL_CLUB_CANONICAL < len(row) else None
        city = row[COL_CITY] if COL_CITY < len(row) else None
        region = row[COL_REGION] if COL_REGION < len(row) else None
        
        # Skip if critical fields missing
        if not city or region is None:
            continue
        
        # Use alt name if present, else canonical
        club_name = club_alt or club_canonical
        if not club_name:
            continue
        
        # Normalize key (uppercase)
        key = str(club_name).strip().upper()
        
        try:
            region_int = int(region)
        except (ValueError, TypeError):
            logger.warning(f"Invalid region for {club_name}: {region}")
            continue
        
        # Store in cache
        _mapping_cache[key] = {
            'city': str(city).strip(),
            'region': region_int,
            'club_canonical': str(club_canonical or club_alt).strip(),
        }
    
    wb.close()
    logger.info(f"Loaded {len(_mapping_cache)} clubs from Excel")


def lookup_club(club_name: str) -> Optional[ClubInfo]:
    """
    Look up club in cached mapping.
    Returns ClubInfo with city/region, or None if not found.
    """
    if not club_name:
        return None
    
    load_mapping()
    
    if _mapping_cache is None:
        return None
    
    key = str(club_name).strip().upper()
    return _mapping_cache.get(key)


def get_missing_clubs(athletes: list) -> set:
    """
    Get set of club names that don't map to a city/region.
    Useful for logging/debugging.
    """
    missing = set()
    for athlete in athletes:
        club_name = athlete.get('club_name')
        if club_name and not lookup_club(club_name):
            missing.add(club_name)
    return missing
```

## Step 2: Test mapping module in isolation

Run:
```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
python -c "
from modules.m4_mapping import lookup_club
result = lookup_club('ANKARA BEL. SK')
print(f'Result: {result}')
print(f'City: {result[\"city\"] if result else \"Not found\"}')
"
```

Expected: Should find "ANKARA BEL. SK" or similar club and return city/region.

## Step 3: Commit

```bash
git add modules/m4_mapping.py
git commit -m "feat: add Excel club → city/region mapping module"
```
