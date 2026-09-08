#!/usr/bin/env python3
"""
generate_static_site.py
------------------------
Builds a static, self-contained copy of the dashboard for GitHub Pages.

It reuses the EXACT same computation path as the live server
(panel/serve.py::serve_api_ranking) — database.db.get_athlete_rankings(),
federasyon.yildizlar_ranker.select_all_yildizlar(), and
panel.serve.apply_selection_status_with_points() — so the static site's
numbers are guaranteed to match what the live dashboard would show.

Output (in docs/, GitHub Pages' default folder):
  docs/index.html        — dashboard shell, unmodified from panel/index.html
  docs/results_data.js   — window.STATIC_DATA = {antalya, edirne, combined, generated_at}
  docs/styles.css        — copied as-is

Run after uploading new LXF results locally, then commit + push:
  python generate_static_site.py
  git add docs/
  git commit -m "chore: static site verisi güncellendi"
  git push
"""

import datetime
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db import get_athlete_rankings
from federasyon.yildizlar_ranker import select_all_yildizlar
from federasyon.gencler_ranker import select_all_gencler
from panel.serve import apply_selection_status_with_points

OUT_DIR = Path(__file__).parent / "docs"
PANEL_DIR = Path(__file__).parent / "panel"

LEGS = ["antalya", "edirne", "combined"]


def _events_to_json(events_dict, times_dict=None):
    """Byte-for-byte identical to serve_api_ranking()'s inline events_to_json
    (same json.dumps call, no ensure_ascii=False, same key/value shape)."""
    result = {}
    for (stroke, distance), points in events_dict.items():
        key = json.dumps([stroke, distance])
        time_text = times_dict.get((stroke, distance), "-") if times_dict else "-"
        result[key] = {"points": points, "time": time_text}
    return result


def build_leg_data(leg: str) -> list:
    """Same pipeline as serve_api_ranking(): full population -> yıldızlar ->
    leg filter -> Federasyon Karması selection -> response shape."""
    athletes = get_athlete_rankings(None, None, None)
    athletes = select_all_yildizlar(athletes)
    athletes = select_all_gencler(athletes)

    if leg == "antalya":
        athletes = [a for a in athletes if len(a["antalya_events"]) > 0]
    elif leg == "edirne":
        athletes = [a for a in athletes if len(a["edirne_events"]) > 0]

    if leg == "combined":
        for a in athletes:
            combined_events_points_only = {}
            for (stroke, dist), data in a.get("combined_events", {}).items():
                points = data.get("points", 0) if isinstance(data, dict) else data
                combined_events_points_only[(stroke, dist)] = points
            a["combined_events_for_ranking"] = combined_events_points_only

    athletes = apply_selection_status_with_points(athletes, leg=leg)

    response = []
    for athlete in athletes:
        if leg == "antalya":
            display_top3 = athlete["antalya_top3"]
        elif leg == "edirne":
            display_top3 = athlete["edirne_top3"]
        else:
            display_top3 = athlete["combined_top3"]

        response.append({
            "athlete_name": athlete["athlete_name"],
            "athlete_id": athlete.get("athlete_id"),
            "birth_year": athlete["birth_year"],
            "gender": athlete["gender"],
            "region": athlete.get("region", 0),
            "city": athlete.get("city", ""),
            "club": athlete.get("club", ""),
            "display_top3": display_top3,
            "antalya_top3": athlete.get("antalya_top3", 0),
            "edirne_top3": athlete.get("edirne_top3", 0),
            "combined_top3": athlete.get("combined_top3", 0),
            "antalya_events": _events_to_json(athlete["antalya_events"], athlete.get("antalya_events_time", {})),
            "edirne_events": _events_to_json(athlete["edirne_events"], athlete.get("edirne_events_time", {})),
            "combined_events": _events_to_json(athlete["combined_events"], athlete.get("combined_events_time", {})),
            "selected": athlete.get("selected", "-"),
            "selected_slot": athlete.get("selected_slot", "-"),
            "selected_federasyon_karma": athlete.get("selected_federasyon_karma", False),
            "multinations": athlete.get("multinations", False),
            "selected_yildiz_multinations": athlete.get("selected_yildiz_multinations", False),
            "candidate_yildiz_multinations": athlete.get("candidate_yildiz_multinations", False),
            "candidate_relay_yildiz_multinations": athlete.get("candidate_relay_yildiz_multinations", False),
            "coach_called_yildiz_multinations": athlete.get("coach_called_yildiz_multinations", False),
            "selected_yildiz_comen_cup_aralik": athlete.get("selected_yildiz_comen_cup_aralik", False),
            "selected_yildiz_comen_cup_nisan": athlete.get("selected_yildiz_comen_cup_nisan", False),
            "candidate_relay_yildiz_comen_cup_aralik": athlete.get("candidate_relay_yildiz_comen_cup_aralik", False),
            "candidate_relay_yildiz_comen_cup_nisan": athlete.get("candidate_relay_yildiz_comen_cup_nisan", False),
            "coach_called_yildiz_comen_cup_aralik": athlete.get("coach_called_yildiz_comen_cup_aralik", False),
            "coach_called_yildiz_comen_cup_nisan": athlete.get("coach_called_yildiz_comen_cup_nisan", False),
            "selected_yildiz_central_europe_aralik": athlete.get("selected_yildiz_central_europe_aralik", False),
            "selected_yildiz_central_europe_nisan": athlete.get("selected_yildiz_central_europe_nisan", False),
            "candidate_yildiz_central_europe_aralik": athlete.get("candidate_yildiz_central_europe_aralik", False),
            "candidate_yildiz_central_europe_nisan": athlete.get("candidate_yildiz_central_europe_nisan", False),
            "candidate_relay_yildiz_central_europe_aralik": athlete.get("candidate_relay_yildiz_central_europe_aralik", False),
            "candidate_relay_yildiz_central_europe_nisan": athlete.get("candidate_relay_yildiz_central_europe_nisan", False),
            "coach_called_yildiz_central_europe_aralik": athlete.get("coach_called_yildiz_central_europe_aralik", False),
            "coach_called_yildiz_central_europe_nisan": athlete.get("coach_called_yildiz_central_europe_nisan", False),
            "selected_multinations_gencler": athlete.get("selected_multinations_gencler", False),
            "candidate_multinations_gencler": athlete.get("candidate_multinations_gencler", False),
            "candidate_relay_multinations_gencler": athlete.get("candidate_relay_multinations_gencler", False),
            "coach_called_multinations_gencler": athlete.get("coach_called_multinations_gencler", False),
            "selected_avrupa_gencler": athlete.get("selected_avrupa_gencler", False),
            "coach_called_avrupa_gencler": athlete.get("coach_called_avrupa_gencler", False),
            "candidate_relay_avrupa_gencler": athlete.get("candidate_relay_avrupa_gencler", False),
            "avrupa_gencler_event_count": len(athlete.get("avrupa_gencler_events", [])),
            "multinations_events": [list(e) for e in athlete.get("multinations_events", [])],
            "comen_cup_events": [list(e) for e in athlete.get("comen_cup_events", [])],
            "central_europe_events": [list(e) for e in athlete.get("central_europe_events", [])],
            "multinations_gencler_events": [list(e) for e in athlete.get("multinations_gencler_events", [])],
            "avrupa_gencler_events": [list(e) for e in athlete.get("avrupa_gencler_events", [])],
        })
    return response


def main():
    OUT_DIR.mkdir(exist_ok=True)

    print("Hesaplanıyor...")
    data = {leg: build_leg_data(leg) for leg in LEGS}
    generated_at = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=3))
    ).strftime("%Y-%m-%d %H:%M (TR)")

    payload = {"generated_at": generated_at, **data}

    js_path = OUT_DIR / "results_data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.STATIC_DATA = ")
        f.write(json.dumps(payload, ensure_ascii=False))
        f.write(";\n")

    shutil.copy(PANEL_DIR / "index.html", OUT_DIR / "index.html")
    shutil.copy(PANEL_DIR / "secilenler.html", OUT_DIR / "secilenler.html")
    styles_src = PANEL_DIR / "styles.css"
    if styles_src.exists():
        shutil.copy(styles_src, OUT_DIR / "styles.css")

    for leg in LEGS:
        print(f"  {leg}: {len(data[leg])} sporcu")
    print(f"\nOK: {js_path} uretildi")
    print(f"OK: {OUT_DIR / 'index.html'} kopyalandi")
    print(f"  Veri zamanı: {generated_at}")


if __name__ == "__main__":
    main()
