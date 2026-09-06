"""
federasyon/tests/test_ranking_determinism.py
-----------------------------------------------
get_athlete_rankings() must return rows in a deterministic order.

Regression: the base fed_results query had no ORDER BY, so SQLite gave no
guarantee about row order across separate connections/processes (even for
identical, unchanged data). Since rank_group()'s tie-break sort is stable
(ties keep whatever order they were handed), an athlete list built in a
different row order could resolve a ranking_key tie differently — e.g. the
same data, queried from two different Python processes, produced different
TR-slot numbers and even a different TR-vs-BÖLGE outcome for tied athletes.
This surfaced comparing the live server's /api/ranking against a
standalone static-site generator script hitting the same database.
"""

import sqlite3

from database.db import get_athlete_rankings


def test_get_athlete_rankings_query_has_deterministic_order():
    """The base fed_results query must include an ORDER BY, not rely on
    incidental SQLite row order (which is not guaranteed to be stable
    across separate connections to the same unchanged data)."""
    import inspect
    from database import db as db_module

    source = inspect.getsource(db_module.get_athlete_rankings)
    assert "ORDER BY" in source, (
        "get_athlete_rankings()'s query must have an explicit ORDER BY — "
        "without one, tie-break results become non-deterministic across "
        "separate connections/processes."
    )


def test_repeated_calls_return_athletes_in_the_same_order(tmp_path):
    """Two separate calls (simulating two separate processes/connections)
    against unchanged data must produce identical athlete ordering — and
    therefore identical tie-break outcomes downstream."""
    from database.db import get_connection

    conn = get_connection()
    try:
        cur = conn.execute("SELECT COUNT(*) FROM fed_results")
        count = cur.fetchone()[0]
    finally:
        conn.close()

    if count == 0:
        import pytest
        pytest.skip("No fed_results data — run an upload first")

    r1 = get_athlete_rankings(None, None, None)
    r2 = get_athlete_rankings(None, None, None)

    names1 = [a["athlete_name"] for a in r1]
    names2 = [a["athlete_name"] for a in r2]
    assert names1 == names2, (
        "get_athlete_rankings() returned athletes in a different order on "
        "a second call against unchanged data — this makes tie-break "
        "results (ranking_key ties, TR vs BÖLGE, slot numbers) "
        "non-deterministic."
    )
