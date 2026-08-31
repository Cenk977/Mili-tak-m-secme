"""
Configuration for Milli Takım Seçme Sistemi
"""

# Competition year
COMPETITION_YEAR = 2026

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

# Age groups for selection
TARGET_BIRTH_YEARS = {2013, 2012, 2011}

# Gender mapping
GENDER_MAP = {
    "Kadın": "F",
    "Erkek": "M"
}
