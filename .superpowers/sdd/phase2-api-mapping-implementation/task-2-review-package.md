# Task 2 Review Package

**Commits:** 1f1f177..333f8fe  
**Task:** Config Updates

## Commit Log

```
333f8fe config: add Excel mapping constants
```

## Diff Summary

```
 config.py | 14 ++++++++++++
 1 file changed, 14 insertions(+), 0 deletions(-)
```

## Full Diff

```diff
diff --git a/config.py b/config.py
index 1456cbf..a852d8c 100644
--- a/config.py
+++ b/config.py
@@ -4,15 +4,29 @@ Configuration for Milli Takım Seçme Sistemi
 
 # Competition year
 COMPETITION_YEAR = 2026
 
 # Database configuration
-DB_PATH = "data/bolge_karmalari.db"
+DB_PATH = "data/selection.db"
 
 # Excel files
 MAPPING_EXCEL_PATH = "Kulüp Şehir Mapping Exceli/Kulüp Şehir Mapping.xlsx"
 
+# ─────────────────────────────────────────────────────────────────────────────
+# Excel Mapping Configuration
+# ─────────────────────────────────────────────────────────────────────────────
+
+MAPPING_SHEET_NAME = "Kulüp-Bölge-Şehir"
+
+# Column indices (0-based)
+# Excel columns: A=0, B=1, C=2, ... G=6
+MAPPING_DATA_START_ROW = 5    # Row 5 (after header rows 1-4)
+COL_CLUB_ALT = 0              # Column A: Kulüp Alternatif
+COL_CLUB_CANONICAL = 2        # Column C: Kulüp Tekil
+COL_CITY = 4                  # Column E: Şehir
+COL_REGION = 6                # Column G: Bölge
+
 # Regions
 REGIONS = {
     1: "İstanbul",
     2: "Marmara",
     3: "Ege",
```
