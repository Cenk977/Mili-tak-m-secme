# -*- coding: utf-8 -*-
"""
generate_static_site.build_leg_data() must expose the same Gençler + *_events
selection fields that /api/ranking does, so the GitHub Pages build of the
dashboard (and secilenler.html) shows the same badges as the live server.
"""
import pytest

import generate_static_site


REQUIRED_KEYS = {
    "selected_multinations_gencler",
    "candidate_multinations_gencler",
    "candidate_relay_multinations_gencler",
    "coach_called_multinations_gencler",
    "selected_avrupa_gencler",
    "coach_called_avrupa_gencler",
    "candidate_relay_avrupa_gencler",
    "avrupa_gencler_event_count",
    "multinations_events",
    "comen_cup_events",
    "central_europe_events",
    "multinations_gencler_events",
    "avrupa_gencler_events",
}


def test_build_leg_data_exposes_gencler_and_events_fields():
    rows = generate_static_site.build_leg_data("combined")
    if not rows:
        pytest.skip("No athlete data in DB — cannot check field shape")
    sample = rows[0]
    missing = REQUIRED_KEYS - set(sample.keys())
    assert not missing, f"static payload missing keys: {sorted(missing)}"
    # *_events must be JSON-friendly list-of-list (or empty list)
    for k in ("multinations_events", "comen_cup_events", "central_europe_events",
              "multinations_gencler_events", "avrupa_gencler_events"):
        assert isinstance(sample[k], list)
        for entry in sample[k]:
            assert isinstance(entry, list) and len(entry) == 2


def test_main_copies_secilenler_html(tmp_path, monkeypatch):
    """main() copies secilenler.html into the static output dir."""
    monkeypatch.setattr(generate_static_site, "OUT_DIR", tmp_path)
    generate_static_site.main()
    assert (tmp_path / "secilenler.html").exists()
    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "results_data.js").exists()
