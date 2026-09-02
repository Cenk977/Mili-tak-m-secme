"""
Central European Countries Meet Yıldızlar 2026 — Antrenor Performance Thresholds

Athletes passing these times qualify for coach invitation.
Same times as Multinations/Comen Cup (per PDF page 7).
"""

ANTRENOR_BARAJLARI = {
    # Format: (stroke, distance) → {"M": time_str, "F": time_str}
    ("Freestyle", 50): {"M": "00:23.41", "F": "00:26.34"},
    ("Freestyle", 100): {"M": "00:51.53", "F": "00:57.33"},
    ("Freestyle", 200): {"M": "01:53.26", "F": "02:04.99"},
    ("Freestyle", 400): {"M": "04:01.40", "F": "04:23.21"},
    ("Freestyle", 800): {"M": None, "F": "09:04.07"},
    ("Freestyle", 1500): {"M": "16:03.90", "F": None},
    ("Backstroke", 50): {"M": "00:26.70", "F": "00:30.12"},
    ("Backstroke", 100): {"M": "00:57.28", "F": "01:04.27"},
    ("Backstroke", 200): {"M": "02:05.25", "F": "02:18.57"},
    ("Breaststroke", 50): {"M": "00:29.09", "F": "00:33.00"},
    ("Breaststroke", 100): {"M": "01:03.96", "F": "01:11.81"},
    ("Breaststroke", 200): {"M": "02:19.32", "F": "02:34.35"},
    ("Butterfly", 50): {"M": "00:25.02", "F": "00:28.01"},
    ("Butterfly", 100): {"M": "00:55.08", "F": "01:02.16"},
    ("Butterfly", 200): {"M": "02:04.45", "F": "02:17.82"},
    ("Medley", 200): {"M": "02:06.79", "F": "02:21.06"},
    ("Medley", 400): {"M": "04:31.78", "F": "04:58.98"},
}

def check_antrenor_baraj(stroke, distance, gender, time_str):
    """
    Check if athlete's time passes antrenor baraj threshold.

    Args:
        stroke: "Freestyle", "Backstroke", "Breaststroke", "Butterfly", "Medley"
        distance: int (50, 100, 200, 400, 800, 1500)
        gender: "M" or "F"
        time_str: time in format "MM:SS.SS"

    Returns:
        bool: True if time <= baraj (passes threshold), False otherwise or if no baraj defined
    """
    key = (stroke, distance)
    if key not in ANTRENOR_BARAJLARI:
        return False

    baraj_time = ANTRENOR_BARAJLARI[key].get(gender)
    if baraj_time is None:
        return False

    # Simple string comparison (works for time format MM:SS.SS)
    return time_str <= baraj_time


if __name__ == "__main__":
    assert check_antrenor_baraj("Freestyle", 50, "M", "00:23.40") == True
    assert check_antrenor_baraj("Freestyle", 50, "M", "00:23.50") == False
    print("OK: Baraj tests pass")
