# -*- coding: utf-8 -*-
"""
2026 Gençler Milli Takım baraj tabloları.
Kaynak: 2026-GENCLER-MILLI-TAKIM-SECILME-KRITERLERI.pdf (s.3 Multi Gençler,
s.5 Avrupa Gençler). Branş adları Türkçe; süreler "MM:SS.ss" / "M:SS.ss".
None = o cinsiyette yarış yok.
"""
from federasyon.yildizlar_ranker import parse_time

# --- Multinations Gençler — Antrenör Barajı (PDF s.3) ---
MULTI_GENCLER_ANTRENOR = {
    ("Serbest", 50):       {"M": "22.84",    "F": "25.69"},
    ("Serbest", 100):      {"M": "50.32",    "F": "55.75"},
    ("Serbest", 200):      {"M": "1:50.51",  "F": "2:01.95"},
    ("Serbest", 400):      {"M": "3:55.85",  "F": "4:17.82"},
    ("Serbest", 800):      {"M": None,       "F": "8:46.98"},
    ("Serbest", 1500):     {"M": "15:37.03", "F": None},
    ("Sırtüstü", 50):      {"M": "26.05",    "F": "29.37"},
    ("Sırtüstü", 100):     {"M": "55.89",    "F": "1:02.39"},
    ("Sırtüstü", 200):     {"M": "2:02.20",  "F": "2:15.61"},
    ("Kurbağalama", 50):   {"M": "28.37",    "F": "32.18"},
    ("Kurbağalama", 100):  {"M": "1:01.87",  "F": "1:09.63"},
    ("Kurbağalama", 200):  {"M": "2:14.87",  "F": "2:30.03"},
    ("Kelebek", 50):       {"M": "24.39",    "F": "27.31"},
    ("Kelebek", 100):      {"M": "53.74",    "F": "1:00.24"},
    ("Kelebek", 200):      {"M": "2:00.41",  "F": "2:13.57"},
    ("Karışık", 200):      {"M": "2:02.66",  "F": "2:16.73"},
    ("Karışık", 400):      {"M": "4:22.60",  "F": "4:49.67"},
}

# --- Avrupa Gençler — Sporcu Barajı (PDF s.5) ---
AVRUPA_GENCLER_SPORCU = {
    ("Serbest", 50):       {"M": "22.84",    "F": "25.81"},
    ("Serbest", 100):      {"M": "50.27",    "F": "56.02"},
    ("Serbest", 200):      {"M": "1:50.51",  "F": "2:01.95"},
    ("Serbest", 400):      {"M": "3:54.15",  "F": "4:17.20"},
    ("Serbest", 800):      {"M": "8:07.21",  "F": "8:45.96"},
    ("Serbest", 1500):     {"M": "15:28.02", "F": "16:43.01"},
    ("Sırtüstü", 50):      {"M": "26.10",    "F": "29.31"},
    ("Sırtüstü", 100):     {"M": "55.89",    "F": "1:02.69"},
    ("Sırtüstü", 200):     {"M": "2:02.20",  "F": "2:16.26"},
    ("Kurbağalama", 50):   {"M": "28.38",    "F": "32.18"},
    ("Kurbağalama", 100):  {"M": "1:02.32",  "F": "1:10.13"},
    ("Kurbağalama", 200):  {"M": "2:15.84",  "F": "2:31.11"},
    ("Kelebek", 50):       {"M": "24.25",    "F": "27.29"},
    ("Kelebek", 100):      {"M": "53.74",    "F": "1:00.53"},
    ("Kelebek", 200):      {"M": "2:00.41",  "F": "2:14.21"},
    ("Karışık", 200):      {"M": "2:02.66",  "F": "2:17.39"},
    ("Karışık", 400):      {"M": "4:22.60",  "F": "4:51.06"},
}

# --- Avrupa Gençler — Antrenör Barajı (PDF s.5, daha sıkı) ---
AVRUPA_GENCLER_ANTRENOR = {
    ("Serbest", 50):       {"M": "22.62",    "F": "25.56"},
    ("Serbest", 100):      {"M": "49.83",    "F": "55.49"},
    ("Serbest", 200):      {"M": "1:49.45",  "F": "2:01.36"},
    ("Serbest", 400):      {"M": "3:51.88",  "F": "4:14.72"},
    ("Serbest", 800):      {"M": "8:02.50",  "F": "8:40.90"},
    ("Serbest", 1500):     {"M": "15:19.01", "F": "16:33.32"},
    ("Sırtüstü", 50):      {"M": "25.54",    "F": "29.13"},
    ("Sırtüstü", 100):     {"M": "55.35",    "F": "1:02.09"},
    ("Sırtüstü", 200):     {"M": "2:01.03",  "F": "2:14.95"},
    ("Kurbağalama", 50):   {"M": "28.00",    "F": "32.08"},
    ("Kurbağalama", 100):  {"M": "1:01.72",  "F": "1:09.46"},
    ("Kurbağalama", 200):  {"M": "2:14.54",  "F": "2:29.67"},
    ("Kelebek", 50):       {"M": "24.10",    "F": "27.12"},
    ("Kelebek", 100):      {"M": "53.22",    "F": "59.95"},
    ("Kelebek", 200):      {"M": "1:59.25",  "F": "2:12.93"},
    ("Karışık", 200):      {"M": "2:01.48",  "F": "2:16.07"},
    ("Karışık", 400):      {"M": "4:20.08",  "F": "4:48.28"},
}


def check_baraj(table, stroke, distance, gender, time_str):
    """time_str baraj süresine eşit veya daha hızlıysa True."""
    row = table.get((stroke, distance))
    if not row:
        return False
    baraj = row.get(gender)
    if baraj is None or not time_str or time_str == "-":
        return False
    return parse_time(time_str) <= parse_time(baraj)


def passes_any(table, athlete, event_times_key="combined_events_time"):
    """Sporcu, yüzdüğü herhangi bir branşta bu tablonun barajını geçiyor mu?"""
    ets = athlete.get(event_times_key, {})
    gender = athlete.get("gender")
    return any(
        check_baraj(table, s, d, gender, ets.get((s, d)))
        for (s, d) in athlete.get("combined_events", {})
    )
