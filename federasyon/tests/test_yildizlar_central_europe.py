"""
federasyon/tests/test_yildizlar_central_europe.py
---------------------------------------------------
Same discretionary-quota issue as Multinations (see
test_yildizlar_multinations.py): Central European's squad quota is 12, but
forcing the squad to exactly 12 by sorting all athletes (including those
with zero wins) and slicing [:12] would include non-winners as if they were
definite selections whenever fewer than 12 athletes actually won an event.
"""

from federasyon.yildizlar_ranker import select_yildizlar_central_europe_aralik


def _athlete(aid, gender, birth_year=2011, events_time=None):
    return {
        'athlete_id': aid,
        'athlete_name': aid,
        'gender': gender,
        'birth_year': birth_year,
        'combined_events_time': events_time or {},
        'combined_events': {},
    }


class TestCentralEuropeKesinVsAday:
    def test_fewer_than_quota_winners_are_not_padded_to_quota(self):
        """3 winners, quota is 12 — only the 3 winners are 'kesin'; the rest
        of the field (no wins) must not be silently selected just to reach
        a squad size of 12."""
        males = [
            _athlete('M1', 'M', events_time={('Serbest', 50): '00:25.00'}),
            _athlete('M2', 'M', events_time={('Serbest', 100): '00:55.00'}),
            _athlete('M3', 'M', events_time={('Sırtüstü', 50): '00:27.00'}),
            # No wins at all (no events swum) — total field (5) is still
            # under the 12-quota, so the old code's sort()+[:12] would keep
            # them anyway since there's nothing to trim.
            _athlete('NoWin1', 'M'),
            _athlete('NoWin2', 'M'),
        ]
        result = select_yildizlar_central_europe_aralik(males)
        selected_count = sum(1 for a in result if a['selected_yildiz_central_europe_aralik'])
        assert selected_count == 3, (
            f"Expected exactly 3 definite selections, got {selected_count} — "
            "squad should not be padded to the 12-athlete quota"
        )
