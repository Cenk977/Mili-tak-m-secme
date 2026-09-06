"""
federasyon/tests/test_yildizlar_comen_cup.py
----------------------------------------------
Comen Cup selection must use the COMBINED (Aralık+Nisan) best result per
event — same as Central European already does — not two independent
per-meet winner checks OR'd together.

Regression: comparing against the real 2026 Comen Cup Mediterranean roster
(11 athletes) showed our system flagging 6 extra "winners" who aren't on
the real roster. Root cause: select_yildizlar_comen_cup_aralik() used
'antalya_events_time' alone and select_yildizlar_comen_cup_nisan() used
'edirne_events_time' alone, so an athlete could "win" in one meet even
though a teammate's COMBINED best time (mixing her better meet per event)
was actually faster overall — creating winners that don't exist when you
correctly take the single best time across both meets, exactly as
Central European's rule requires ("Aralık ve Nisan seçme müsabakalarından
seçilecektir" — one pooled result set, not two separate contests).
"""

from federasyon.yildizlar_ranker import select_yildizlar_comen_cup_aralik


def _athlete(aid, gender, birth_year=2011, antalya_time=None, edirne_time=None):
    return {
        'athlete_id': aid,
        'athlete_name': aid,
        'gender': gender,
        'birth_year': birth_year,
        'antalya_events_time': antalya_time or {},
        'edirne_events_time': edirne_time or {},
        'combined_events_time': {**(antalya_time or {}), **(edirne_time or {})},
        'combined_events': {},
    }


class TestComenCupUsesCombinedBestResult:
    def test_athlete_who_only_wins_one_of_two_separate_meets_is_not_selected_if_teammate_faster_overall(self):
        """A: fast in Antalya (27.00), mediocre in Edirne (28.50) -> best 27.00.
        B: mediocre in Antalya (27.50), fast in Edirne (26.90) -> best 26.90.
        Combined best-of-both-meets: B is the true winner (26.90 < 27.00).
        The old per-meet-only logic would ALSO select A (winner of the
        Antalya-only comparison) even though A's combined best time loses
        to B's combined best time — that extra, incorrect selection is
        exactly the bug found comparing against the real Comen roster."""
        event = ('Serbest', 50)
        females = [
            _athlete('A', 'F', antalya_time={event: '00:27.00'}, edirne_time={event: '00:28.50'}),
            _athlete('B', 'F', antalya_time={event: '00:27.50'}, edirne_time={event: '00:26.90'}),
        ]
        result = select_yildizlar_comen_cup_aralik(females)
        by_id = {a['athlete_id']: a for a in result}

        assert by_id['B']['selected_yildiz_comen_cup_aralik'] is True
        assert by_id['A']['selected_yildiz_comen_cup_aralik'] is False, (
            "A should NOT be selected: A's best across both meets (27.00) "
            "loses to B's combined best (26.90) — selection must be based "
            "on one pooled combined-best-time ranking, not two independent "
            "per-meet winner checks"
        )
