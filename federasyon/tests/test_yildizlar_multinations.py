"""
federasyon/tests/test_yildizlar_multinations.py
------------------------------------------------
Multinations selection has two tiers per the federation rule text
("...federasyon tarafından kadroya davet edilebilir" — CAN be invited,
not MUST): athletes with an actual 1st place are definite (kesin);
padding the squad up to the 10-athlete quota with 2nd/3rd-place athletes
is the federation's own discretionary call, not an algorithmic one.

Regression: the old code always forced the squad to exactly 10 by padding
with 2nd/3rd-place athletes even when fewer than 10 athletes had a real
1st place — comparison against the official 2026MULTIYILDIZ.pdf roster
showed this over-selected 2 men who aren't on the real roster (the
federation left the men's squad at 8, its own discretionary choice not to
pad to 10).
"""

from federasyon.yildizlar_ranker import select_yildizlar_multinations


def _athlete(aid, gender, birth_year=2011, events_time=None):
    return {
        'athlete_id': aid,
        'athlete_name': aid,
        'gender': gender,
        'birth_year': birth_year,
        'antalya_events_time': events_time or {},
        'combined_events': {},
        'combined_events_time': {},
    }


class TestMultinationsKesinVsAday:
    def test_fewer_than_quota_winners_are_not_padded_to_quota(self):
        """3 male winners, quota is 10 — only the 3 winners are 'kesin'.
        2nd/3rd-place athletes become 'aday' (candidate), not selected."""
        males = [
            _athlete('M1', 'M', events_time={('Serbest', 50): '00:25.00'}),  # wins
            _athlete('M2', 'M', events_time={('Serbest', 50): '00:26.00'}),  # 2nd
            _athlete('M3', 'M', events_time={('Serbest', 100): '00:55.00'}),  # wins
            _athlete('M4', 'M', events_time={('Serbest', 100): '00:56.00'}),  # 2nd
            _athlete('M5', 'M', events_time={('Sırtüstü', 50): '00:27.00'}),  # wins
        ]
        result = select_yildizlar_multinations(males)
        by_id = {a['athlete_id']: a for a in result}

        assert by_id['M1']['selected_yildiz_multinations'] is True
        assert by_id['M3']['selected_yildiz_multinations'] is True
        assert by_id['M5']['selected_yildiz_multinations'] is True

        # Only 3 real winners — must NOT be padded to quota (10) by
        # auto-selecting the 2nd-place athletes as if they were chosen.
        selected_count = sum(1 for a in result if a['selected_yildiz_multinations'])
        assert selected_count == 3, (
            f"Expected exactly 3 definite selections (real 1st places), "
            f"got {selected_count} — squad should not be force-padded to quota"
        )

        # 2nd-place athletes are candidates, not selected
        assert by_id['M2']['selected_yildiz_multinations'] is False
        assert by_id['M2'].get('candidate_yildiz_multinations') is True
        assert by_id['M4']['selected_yildiz_multinations'] is False
        assert by_id['M4'].get('candidate_yildiz_multinations') is True

    def test_relay_leg_candidate_flagged_even_when_quota_already_full(self):
        """An athlete with NO individual win, but a top-6 time in a 100m/200m
        event that maps to a relay leg (Sırtüstü/Kurbağalama/Kelebek/Serbest
        100, or Serbest 200 — the distances Multinations relays actually
        swim), should be flagged as a relay candidate — independent of
        whether the individual-event quota is already filled by winners.

        Real-world case that motivated this: Ayşe Nazlı Sönmez had zero
        individual wins in the 2026 Aralık data (11 other women already won
        events, filling the 10-woman quota), yet she made the official
        published Multinations roster — she ranked competitively in 100m
        Serbest/Kelebek, which the individual-win-only algorithm couldn't
        explain, but which lines up with relay-leg depth."""
        females = [
            _athlete('W1', 'F', events_time={('Serbest', 50): '00:27.00',
                                              ('Serbest', 100): '00:58.00'}),  # wins both events
            _athlete('W2', 'F', events_time={('Serbest', 50): '00:27.50',
                                              ('Serbest', 100): '00:59.00'}),  # no win, but 2nd-fastest 100 free
            _athlete('W3', 'F', events_time={('Serbest', 50): '00:28.00',
                                              ('Serbest', 100): '01:10.00'}),  # no win, far outside relay-leg depth
        ] + [
            # Filler swimmers, all faster than W3 in 100 free, so W3's rank
            # there is well outside the top-6 relay-candidate cutoff.
            _athlete(f'Filler{i}', 'F', events_time={('Serbest', 100): f'00:{60+i}.00'})
            for i in range(1, 7)
        ]
        result = select_yildizlar_multinations(females)
        by_id = {a['athlete_id']: a for a in result}

        assert by_id['W1']['selected_yildiz_multinations'] is True
        # W2 has no win but a competitive 100 free time -> relay candidate
        assert by_id['W2'].get('candidate_relay_yildiz_multinations') is True
        assert by_id['W2']['selected_yildiz_multinations'] is False
        # W3 has neither a win nor a competitive relay-leg time
        assert by_id['W3'].get('candidate_relay_yildiz_multinations') is False

    def test_winner_with_no_second_or_third_place_is_not_marked_candidate(self):
        """An athlete with zero wins AND zero 2nd/3rd places should not be
        flagged as a candidate — nothing supports inviting them."""
        males = [
            _athlete('M1', 'M', events_time={('Serbest', 50): '00:25.00'}),
            _athlete('M2', 'M', events_time={}),  # no results at all
        ]
        result = select_yildizlar_multinations(males)
        by_id = {a['athlete_id']: a for a in result}
        assert by_id['M2']['selected_yildiz_multinations'] is False
        assert by_id['M2'].get('candidate_yildiz_multinations') is False
