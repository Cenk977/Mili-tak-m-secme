# -*- coding: utf-8 -*-
"""
Türk plaka kodu (01-81) -> bölge / il eşlemesi.

LXF dosyalarında kulüpsüz ("Ferdi") sporcular Excel kulüp haritasında
bulunmaz; ancak CLUB düğümü sporcunun ilini plaka kodu olarak taşır
(örn. <CLUB name="Ferdi" nation="TUR" region="07">). Bu modül o kodu
projenin 6 bölgeli seçim şemasına çevirir.

PLATE_TO_REGION, modules/m4_mapping.py'nin Excel il->bölge verisinden
üretilmiştir (81/81 il, eksik yok).
"""
from typing import Optional

PLATE_TO_PROVINCE = {
    1: "Adana", 2: "Adıyaman", 3: "Afyonkarahisar", 4: "Ağrı", 5: "Amasya",
    6: "Ankara", 7: "Antalya", 8: "Artvin", 9: "Aydın", 10: "Balıkesir",
    11: "Bilecik", 12: "Bingöl", 13: "Bitlis", 14: "Bolu", 15: "Burdur",
    16: "Bursa", 17: "Çanakkale", 18: "Çankırı", 19: "Çorum", 20: "Denizli",
    21: "Diyarbakır", 22: "Edirne", 23: "Elazığ", 24: "Erzincan", 25: "Erzurum",
    26: "Eskişehir", 27: "Gaziantep", 28: "Giresun", 29: "Gümüşhane", 30: "Hakkari",
    31: "Hatay", 32: "Isparta", 33: "Mersin", 34: "İstanbul", 35: "İzmir",
    36: "Kars", 37: "Kastamonu", 38: "Kayseri", 39: "Kırklareli", 40: "Kırşehir",
    41: "Kocaeli", 42: "Konya", 43: "Kütahya", 44: "Malatya", 45: "Manisa",
    46: "Kahramanmaraş", 47: "Mardin", 48: "Muğla", 49: "Muş", 50: "Nevşehir",
    51: "Niğde", 52: "Ordu", 53: "Rize", 54: "Sakarya", 55: "Samsun",
    56: "Siirt", 57: "Sinop", 58: "Sivas", 59: "Tekirdağ", 60: "Tokat",
    61: "Trabzon", 62: "Tunceli", 63: "Şanlıurfa", 64: "Uşak", 65: "Van",
    66: "Yozgat", 67: "Zonguldak", 68: "Aksaray", 69: "Bayburt", 70: "Karaman",
    71: "Kırıkkale", 72: "Batman", 73: "Şırnak", 74: "Bartın", 75: "Ardahan",
    76: "Iğdır", 77: "Yalova", 78: "Karabük", 79: "Kilis", 80: "Osmaniye",
    81: "Düzce",
}

PLATE_TO_REGION = {
    1: 6, 2: 6, 3: 3, 4: 6, 5: 4, 6: 4, 7: 3, 8: 5, 9: 3, 10: 3,
    11: 2, 12: 6, 13: 6, 14: 4, 15: 3, 16: 2, 17: 2, 18: 4, 19: 4, 20: 3,
    21: 6, 22: 2, 23: 6, 24: 5, 25: 5, 26: 4, 27: 6, 28: 5, 29: 5, 30: 6,
    31: 6, 32: 3, 33: 6, 34: 1, 35: 3, 36: 6, 37: 4, 38: 4, 39: 2, 40: 4,
    41: 2, 42: 4, 43: 3, 44: 6, 45: 3, 46: 6, 47: 6, 48: 3, 49: 6, 50: 4,
    51: 4, 52: 5, 53: 5, 54: 2, 55: 5, 56: 6, 57: 5, 58: 4, 59: 2, 60: 4,
    61: 5, 62: 6, 63: 6, 64: 3, 65: 6, 66: 4, 67: 4, 68: 4, 69: 5, 70: 4,
    71: 4, 72: 6, 73: 6, 74: 5, 75: 6, 76: 6, 77: 2, 78: 4, 79: 6, 80: 6,
    81: 2,
}


def _normalize(code) -> Optional[int]:
    """'07' / 7 / ' 7 ' -> 7; geçersizse None."""
    if code is None:
        return None
    try:
        return int(str(code).strip())
    except (ValueError, TypeError):
        return None


def plate_to_region(code) -> Optional[int]:
    """Plaka kodundan bölge numarası (1-6). Bilinmiyorsa None."""
    return PLATE_TO_REGION.get(_normalize(code))


def plate_to_province(code) -> Optional[str]:
    """Plaka kodundan il adı. Bilinmiyorsa None."""
    return PLATE_TO_PROVINCE.get(_normalize(code))
