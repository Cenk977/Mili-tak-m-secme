"""
Configuration for Milli Takım Seçme Sistemi
"""

# Competition year
COMPETITION_YEAR = 2026

# Database configuration
DB_PATH = "data/bolge_karmalari.db"

# Excel files
MAPPING_EXCEL_PATH = "Kulüp Şehir Mapping Exceli/Kulüp Şehir Mapping.xlsx"

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
