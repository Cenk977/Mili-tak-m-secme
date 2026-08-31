# Task 2: Config Updates

**Files:**
- Modify: `config.py`

**Interfaces:**
- Produces:
  - `MAPPING_EXCEL_PATH: str` (path to Excel file)
  - `MAPPING_SHEET_NAME: str` (sheet name in Excel)
  - `MAPPING_DATA_START_ROW: int` (row where data starts)
  - `COL_CLUB_ALT: int` (column index for alternate club name)
  - `COL_CLUB_CANONICAL: int` (column index for canonical club name)
  - `COL_CITY: int` (column index for city)
  - `COL_REGION: int` (column index for region)

## Step 1: Read current config.py and add mapping constants

Add to `config.py` after existing constants:

```python
# ─────────────────────────────────────────────────────────────────────────────
# Excel Mapping Configuration
# ─────────────────────────────────────────────────────────────────────────────

MAPPING_EXCEL_PATH = "Kulüp Şehir Mapping Exceli/Kulüp Şehir Mapping.xlsx"
MAPPING_SHEET_NAME = "Kulüp-Bölge-Şehir"

# Column indices (0-based)
# Excel columns: A=0, B=1, C=2, ... G=6
MAPPING_DATA_START_ROW = 5    # Row 5 (after header rows 1-4)
COL_CLUB_ALT = 0              # Column A: Kulüp Alternatif
COL_CLUB_CANONICAL = 2        # Column C: Kulüp Tekil
COL_CITY = 4                  # Column E: Şehir
COL_REGION = 6                # Column G: Bölge
```

## Step 2: Commit

```bash
git add config.py
git commit -m "config: add Excel mapping constants"
```
