"""
Configuration for Milli Takım Seçme Sistemi
"""

# Competition year
COMPETITION_YEAR = 2027

# Database configuration
DB_PATH = "data/selection.db"

# Excel files
MAPPING_EXCEL_PATH = "Kulüp Şehir Mapping Exceli/Kulüp Şehir Mapping.xlsx"

# ─────────────────────────────────────────────────────────────────────────────
# Excel Mapping Configuration
# ─────────────────────────────────────────────────────────────────────────────

MAPPING_SHEET_NAME = "Kulüp-Bölge-Şehir"

# Column indices (0-based)
# Excel columns: A=0, B=1, C=2, ... G=6
MAPPING_DATA_START_ROW = 5    # Row 5 (after header rows 1-4)
COL_CLUB_ALT = 0              # Column A: Kulüp Alternatif
COL_CLUB_CANONICAL = 2        # Column C: Kulüp Tekil
COL_CITY = 4                  # Column E: Şehir
COL_REGION = 6                # Column G: Bölge

# Regions
REGIONS = {
    1: "İstanbul",
    2: "Marmara",
    3: "Ege",
    4: "İç Anadolu",
    5: "Karadeniz",
    6: "Güneydoğu"
}

# Stroke mapping
STROKE_MAP = {
    "FREE": "Serbest",
    "BACK": "Sırtüstü",
    "BREAST": "Kurbağalama",
    "FLY": "Kelebek",
    "MEDLEY": "Karışık"
}

# Age groups for selection (2027: 14, 13, 12-year-olds)
TARGET_AGE_GROUPS = {2014, 2013, 2012}
TARGET_BIRTH_YEARS = TARGET_AGE_GROUPS  # backward compatibility

# Selection quotas for national team (per age group)
SELECTION_QUOTAS = {
    2014: {
        "tr": 8,
        "region_1": 3,
        "region_other": 2,
        "min_points": 7
    },
    2013: {
        "tr": 8,
        "region_1": 3,
        "region_other": 2,
        "min_points": 7
    },
    2012: {
        "tr": 8,
        "region_1": 3,
        "region_other": 2,
        "min_points": 7
    }
}

# Scoring points system (baraj)
POINTS = [1, 2, 3, 4, 5, 6, 7, 9]  # 8 is skipped, matches reference system

# Gender mapping
GENDER_MAP = {
    "Kadın": "F",
    "Erkek": "M"
}
