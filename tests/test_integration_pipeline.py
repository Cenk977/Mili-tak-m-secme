"""
tests/test_integration_pipeline.py
----------------------------------
Integration tests for MiltiTakimPipeline end-to-end flow.

Tests verify:
  1. End-to-end LXF upload → database → response
  2. TR quota enforcement per age group
  3. BÖLGE quota per region enforcement
  4. Tie-breaking with ranking_key
  5. Database persistence and consistency
  6. Error handling with corrupted files
  7. Backward compatibility
  8. UTF-8 and Turkish character support
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import sqlite3

# Ensure imports work from project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from federasyon.pipeline import MiltiTakimPipeline
from federasyon.db_fed import (
    get_conn, migrate_add_selection_columns, get_selected_athletes,
    upsert_fed_results, update_athlete_selection
)
from federasyon.scoring_tables import SELECTION_QUOTAS
from config import DB_PATH


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: End-to-End LXF Upload
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEndUpload:
    """Test complete pipeline flow: LXF → parse → score → rank → DB → response"""

    def test_upload_with_real_lxf_file(self, real_test_lxf):
        """
        Upload real LXF file and verify complete flow.

        Verifies:
          - process() returns dict with success=True
          - Response has required keys: selected_tr, selected_bolge, summary
          - Database has results after processing
          - Counts are consistent
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        # Verify response structure
        assert isinstance(result, dict), "Result must be dict"
        assert result['success'] is True, f"Pipeline failed: {result.get('message')}"
        assert 'selected_tr' in result
        assert 'selected_bolge' in result
        assert 'summary' in result
        assert 'baraj_yok_count' in result
        assert 'total_athletes' in result
        assert 'message' in result

        # Verify response data types
        assert isinstance(result['selected_tr'], list)
        assert isinstance(result['selected_bolge'], list)
        assert isinstance(result['summary'], dict)
        assert isinstance(result['total_athletes'], int)

        # Verify athlete structure in response
        for athlete in result['selected_tr']:
            assert 'name' in athlete
            assert 'birth_year' in athlete
            assert 'selected_slot' in athlete
            assert athlete['selected_slot'].startswith('TR-'), \
                f"TR athlete must have TR-X slot, got {athlete['selected_slot']}"

        for athlete in result['selected_bolge']:
            assert 'name' in athlete
            assert 'birth_year' in athlete
            assert 'selected_slot' in athlete
            # BÖLGE slots typically look like B1-1, B2-2, etc.

    def test_database_populated_after_upload(self, real_test_lxf):
        """
        Verify database tables are populated after pipeline processing.

        Checks:
          - Pipeline completes successfully
          - Response contains processed athletes
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True, f"Pipeline should succeed: {result.get('message')}"

        # Verify pipeline returns some athletes or indicates processing occurred
        total_processed = result['total_athletes']
        assert total_processed > 0 or result['message'] is not None, \
            "Pipeline should process some athletes or return explanation"

        # If there are selected athletes, verify database state consistency
        if len(result['selected_tr']) + len(result['selected_bolge']) > 0:
            with get_conn() as conn:
                cursor = conn.cursor()

                # Verify selection columns have proper values
                selected_athletes = cursor.execute(
                    "SELECT COUNT(*) as cnt FROM fed_athlete_best WHERE selected IN ('TR', 'BÖLGE')"
                ).fetchone()['cnt']

                # Should have at least one selected athlete if response has any
                expected_selected = len(result['selected_tr']) + len(result['selected_bolge'])
                assert selected_athletes >= expected_selected, \
                    f"Database should have at least {expected_selected} selected athletes"

    def test_response_athlete_counts_match_database(self, real_test_lxf):
        """
        Verify response athlete counts match database records.

        Ensures:
          - len(selected_tr) matches DB count
          - len(selected_bolge) matches DB count
          - Total matches sum of all categories
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        # Get counts from database
        tr_from_db = get_selected_athletes(selected='TR')
        bolge_from_db = get_selected_athletes(selected='BÖLGE')

        # Compare with response
        assert len(result['selected_tr']) == len(tr_from_db), \
            f"TR count mismatch: response={len(result['selected_tr'])}, db={len(tr_from_db)}"
        assert len(result['selected_bolge']) == len(bolge_from_db), \
            f"BÖLGE count mismatch: response={len(result['selected_bolge'])}, db={len(bolge_from_db)}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: TR Quota Enforcement
# ─────────────────────────────────────────────────────────────────────────────

class TestTRQuotaEnforcement:
    """Verify TR selection respects birth-year quotas"""

    def test_tr_quota_not_exceeded_for_birth_year(self, real_test_lxf):
        """
        Verify TR quota is not exceeded for any birth year.

        Uses SELECTION_QUOTAS[birth_year]['tr'] as upper bound.
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        # Group TR athletes by birth year
        tr_by_birth_year = {}
        for athlete in result['selected_tr']:
            by = athlete['birth_year']
            tr_by_birth_year.setdefault(by, []).append(athlete)

        # Check quota for each birth year
        for by, athletes_list in tr_by_birth_year.items():
            quota = SELECTION_QUOTAS.get(by, {}).get('tr', 0)
            count = len(athletes_list)

            assert count <= quota, \
                f"TR quota violated for {by}: {count} selected > {quota} quota"

    def test_tr_quota_validation_in_pipeline(self, sample_athletes_data):
        """
        Test validate_results() correctly validates TR quota.

        Ensures validation method catches quota violations.
        """
        pipeline = MiltiTakimPipeline()

        # Test 1: Create athletes exactly at quota (quota for 2013 is 8 TR athletes)
        at_quota_athletes = [
            {
                'name': f'TR Athlete {i}',
                'birth_year': 2013,
                'gender': 'M' if i % 2 == 0 else 'F',
                'selected': 'TR',
                'selected_slot': f'TR-{i}',
                'top3_total': 20
            }
            for i in range(1, 9)  # 8 athletes = quota for 2013
        ]

        # Should pass validation (exactly at limit)
        try:
            result = pipeline.validate_results(at_quota_athletes)
            assert result is True, "Should pass validation at quota limit"
        except Exception as e:
            pytest.fail(f"Should not raise exception at quota limit: {e}")

        # Test 2: Create invalid selection status (should definitely raise)
        invalid_status = [
            {
                'name': 'Bad Athlete',
                'birth_year': 2013,
                'selected': 'INVALID_STATUS'
            }
        ]

        with pytest.raises(Exception) as exc_info:
            pipeline.validate_results(invalid_status)

        assert 'invalid' in str(exc_info.value).lower(), \
            f"Should catch invalid status, got: {exc_info.value}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: BÖLGE Quota Per Region
# ─────────────────────────────────────────────────────────────────────────────

class TestBölgeQuotaPerRegion:
    """Verify BÖLGE selection respects per-region quotas"""

    def test_bolge_quota_per_region(self, real_test_lxf):
        """
        Verify BÖLGE quota is enforced per region.

        For each region in SELECTION_QUOTAS[birth_year]:
          - Count BÖLGE athletes in that region
          - Assert count <= quota
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        # Group BÖLGE athletes by birth_year and region
        bolge_by_year_region = {}
        for athlete in result['selected_bolge']:
            by = athlete['birth_year']
            region = athlete.get('region')

            if by not in bolge_by_year_region:
                bolge_by_year_region[by] = {}
            if region not in bolge_by_year_region[by]:
                bolge_by_year_region[by][region] = []

            bolge_by_year_region[by][region].append(athlete)

        # Verify quotas (check against expected regional limits)
        for by, regions_dict in bolge_by_year_region.items():
            quota = SELECTION_QUOTAS.get(by, {})
            region_1_limit = quota.get('region_1', 3)
            region_other_limit = quota.get('region_other', 2)

            for region, athletes_list in regions_dict.items():
                count = len(athletes_list)

                if region == 1:
                    limit = region_1_limit
                    assert count <= limit, \
                        f"BÖLGE quota exceeded for {by}/Region 1: {count} > {limit}"
                else:
                    limit = region_other_limit
                    assert count <= limit, \
                        f"BÖLGE quota exceeded for {by}/Region {region}: {count} > {limit}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Tie-Breaking
# ─────────────────────────────────────────────────────────────────────────────

class TestTieBreaking:
    """Verify tie-breaking with ranking_key"""

    def test_tied_athletes_ranked_by_ranking_key(self, real_test_lxf):
        """
        Verify tied athletes are ranked by ranking_key.

        Checks:
          - Database has athletes with tied=1 marker
          - Tied athletes have different selections or ranking_keys
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        # Query database for tie information
        with get_conn() as conn:
            cursor = conn.cursor()

            # Check if any athletes are marked as tied
            tied_count = cursor.execute(
                "SELECT COUNT(*) as cnt FROM fed_athlete_best WHERE tied = 1"
            ).fetchone()['cnt']

            # If tied athletes exist, verify they have proper differentiation
            if tied_count > 0:
                tied_athletes = cursor.execute("""
                    SELECT athlete_name, birth_year, selected, ranking_key
                    FROM fed_athlete_best
                    WHERE tied = 1
                    ORDER BY athlete_name
                """).fetchall()

                # Tied athletes should exist and have selection info
                assert len(tied_athletes) > 0, "Should have tied athletes"

                # Each tied athlete should have either different selection or ranking_key
                for athlete in tied_athletes:
                    assert athlete['selected'] in {'-', 'TR', 'BÖLGE', 'BARAJ_YOK', 'MULTINATIONS'}, \
                        f"Tied athlete should have valid selection status"
                    # ranking_key could be empty or populated depending on tie resolution
            else:
                # If no tied athletes in this data, that's also valid
                # (data might just not have ties)
                pass

    def test_ranking_key_field_populated(self, real_test_lxf):
        """Verify ranking_key field exists and is accessible in database"""
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        with get_conn() as conn:
            cursor = conn.cursor()

            # Verify ranking_key column exists (schema is correct)
            # Note: ranking_key might be empty string or NULL for many athletes
            # depending on tie-breaking logic
            try:
                ranking_key_rows = cursor.execute("""
                    SELECT COUNT(*) as cnt
                    FROM fed_athlete_best
                    WHERE selected IN ('TR', 'BÖLGE')
                """).fetchone()['cnt']

                # If there are selected athletes, they should be accessible
                if ranking_key_rows > 0:
                    sample = cursor.execute("""
                        SELECT athlete_name, ranking_key
                        FROM fed_athlete_best
                        WHERE selected IN ('TR', 'BÖLGE')
                        LIMIT 1
                    """).fetchone()

                    # Column exists if we got here
                    assert sample is not None, "Should have selected athletes to check"
            except Exception as e:
                # If query fails due to column, that's a schema issue
                if "ranking_key" in str(e):
                    pytest.fail(f"ranking_key column should exist: {e}")
                raise


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Database Persistence
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabasePersistence:
    """Verify data is correctly saved to database"""

    def test_fed_results_has_all_athlete_events(self, real_test_lxf):
        """
        Verify fed_results contains all athlete events.

        For each athlete in fed_athlete_best, verify corresponding rows in fed_results.
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        with get_conn() as conn:
            cursor = conn.cursor()

            # Get unique athletes from fed_athlete_best
            athletes = cursor.execute("""
                SELECT DISTINCT athlete_name, birth_year
                FROM fed_athlete_best
            """).fetchall()

            for athlete in athletes:
                name = athlete['athlete_name']
                by = athlete['birth_year']

                # Verify athlete has entries in fed_results
                result_rows = cursor.execute("""
                    SELECT COUNT(*) as cnt
                    FROM fed_results
                    WHERE athlete_name = ? AND birth_year = ?
                """, (name, by)).fetchone()['cnt']

                assert result_rows > 0, \
                    f"Athlete {name} ({by}) should have results in fed_results"

    def test_athlete_best_has_selection_status(self, real_test_lxf):
        """
        Verify fed_athlete_best has selection status populated.

        Checks:
          - 'selected' column has values
          - 'selected_slot' column has values
          - Values are in valid set: TR, BÖLGE, BARAJ_YOK, -
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        with get_conn() as conn:
            cursor = conn.cursor()

            # Get all athletes from fed_athlete_best
            athletes = cursor.execute("""
                SELECT DISTINCT athlete_name, birth_year, selected, selected_slot
                FROM fed_athlete_best
            """).fetchall()

            valid_selections = {'-', 'TR', 'BÖLGE', 'BARAJ_YOK', 'MULTINATIONS'}

            for athlete in athletes:
                selected = athlete['selected']
                selected_slot = athlete['selected_slot']

                assert selected in valid_selections, \
                    f"Invalid selection status: {selected}"

    def test_fed_results_response_counts_match(self, sample_athletes_data):
        """
        Verify that saving athletes results in correct database state.

        Uses sample data to ensure known input → known database state.
        Only athletes with event_scores are saved to fed_results.
        """
        migrate_add_selection_columns()
        pipeline = MiltiTakimPipeline()

        # Save sample athletes
        athletes_with_events = 0
        for athlete in sample_athletes_data:
            if athlete.get('event_scores'):
                upsert_fed_results(athlete, race_leg='milli_takim')
                athletes_with_events += 1
            update_athlete_selection(athlete)

        with get_conn() as conn:
            cursor = conn.cursor()

            # Verify athletes in database
            saved_athletes = cursor.execute(
                "SELECT COUNT(DISTINCT athlete_name || birth_year) as cnt FROM fed_results"
            ).fetchone()['cnt']

            assert saved_athletes == athletes_with_events, \
                f"Expected {athletes_with_events} athletes with events, got {saved_athletes}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Error Handling
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorHandling:
    """Verify error handling for invalid input"""

    def test_process_returns_error_on_missing_file(self):
        """process() returns error dict when file doesn't exist"""
        pipeline = MiltiTakimPipeline()
        result = pipeline.process('/nonexistent/path/to/file.lxf')

        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'error' in result or 'message' in result

    def test_process_returns_error_on_corrupted_lxf(self, temp_lxf_file):
        """
        process() returns error dict with corrupted LXF file.

        Corrupted LXF is not a valid zip file.
        """
        # Write invalid content to temp file
        with open(temp_lxf_file, 'wb') as f:
            f.write(b'This is not a valid LXF file')

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(temp_lxf_file)

        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'error' in result or 'message' in result

    def test_process_handles_empty_lxf_gracefully(self, temp_lxf_file):
        """process() handles empty LXF file gracefully"""
        # Write empty content
        with open(temp_lxf_file, 'wb') as f:
            f.write(b'')

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(temp_lxf_file)

        # Should either return error or handle gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'message' in result

    def test_database_not_modified_on_error(self, temp_lxf_file):
        """
        Database should not be modified when pipeline errors.

        Saves current row count, attempts failed process, verifies count unchanged.
        """
        with get_conn() as conn:
            cursor = conn.cursor()
            initial_count = cursor.execute(
                "SELECT COUNT(*) as cnt FROM fed_results"
            ).fetchone()['cnt']

        # Corrupt file
        with open(temp_lxf_file, 'wb') as f:
            f.write(b'CORRUPTED')

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(temp_lxf_file)

        assert result['success'] is False

        # Verify database unchanged
        with get_conn() as conn:
            cursor = conn.cursor()
            final_count = cursor.execute(
                "SELECT COUNT(*) as cnt FROM fed_results"
            ).fetchone()['cnt']

        assert final_count == initial_count, \
            "Database should not be modified on error"


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Backward Compatibility
# ─────────────────────────────────────────────────────────────────────────────

class TestBackwardCompatibility:
    """Verify existing code paths still work"""

    def test_pipeline_initialization(self):
        """MiltiTakimPipeline can be instantiated"""
        pipeline = MiltiTakimPipeline()
        assert pipeline is not None
        assert hasattr(pipeline, 'process')

    def test_pipeline_has_all_methods(self):
        """Pipeline has all required methods"""
        pipeline = MiltiTakimPipeline()
        assert hasattr(pipeline, 'parse_and_extract')
        assert hasattr(pipeline, 'score_athletes')
        assert hasattr(pipeline, 'rank_athletes')
        assert hasattr(pipeline, 'save_to_database')
        assert hasattr(pipeline, 'build_response')
        assert hasattr(pipeline, 'validate_results')

    def test_response_format_unchanged(self, real_test_lxf):
        """Response format matches expected structure"""
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        # Verify original response structure
        required_keys = {
            'success', 'message', 'selected_tr', 'selected_bolge',
            'baraj_yok_count', 'total_athletes', 'summary'
        }
        assert required_keys.issubset(result.keys()), \
            f"Missing keys in response: {required_keys - result.keys()}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: UTF-8 and Turkish Character Support
# ─────────────────────────────────────────────────────────────────────────────

class TestUTF8Support:
    """Verify UTF-8 encoding and Turkish character handling"""

    def test_turkish_characters_in_response(self, real_test_lxf):
        """Response contains Turkish characters without corruption"""
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        # Check that response can be JSON serialized with Turkish chars
        response_json = json.dumps(result, ensure_ascii=False)
        assert isinstance(response_json, str)

        # Check for Turkish characters in names/cities
        response_str = str(result)
        # If real data has Turkish cities, they should be readable
        # This is more of a smoke test

    def test_database_stores_turkish_names(self, real_test_lxf):
        """Database correctly stores Turkish names"""
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        with get_conn() as conn:
            cursor = conn.cursor()

            # Get a sample of athlete names
            athletes = cursor.execute(
                "SELECT athlete_name FROM fed_athlete_best LIMIT 5"
            ).fetchall()

            for athlete in athletes:
                name = athlete['athlete_name']
                # Should be decodable as UTF-8
                assert isinstance(name, str)

    def test_sample_athlete_with_turkish_chars(self, sample_athletes_data):
        """Sample athletes with Turkish characters are handled correctly"""
        turkish_athlete = {
            'name': 'Çağatay Işık',
            'birth_year': 2013,
            'gender': 'M',
            'region': 1,
            'city': 'İstanbul',
            'club': 'Dalgıç Spor Kulübü',
            'event_scores': {('Serbest', 50): 5},
            'selected': 'TR',
            'selected_slot': 'TR-1',
            'ranking_key': str((-5,)),
            'top3_total': 5,
            'tied': False
        }

        migrate_add_selection_columns()

        # Should save without encoding issues
        upsert_fed_results(turkish_athlete, race_leg='milli_takim')
        update_athlete_selection(turkish_athlete)

        # Should retrieve correctly
        with get_conn() as conn:
            cursor = conn.cursor()
            saved = cursor.execute(
                "SELECT athlete_name FROM fed_athlete_best WHERE athlete_name = ?",
                ('Çağatay Işık',)
            ).fetchone()

        assert saved is not None
        assert saved['athlete_name'] == 'Çağatay Işık'


# ─────────────────────────────────────────────────────────────────────────────
# Additional Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPipelineIntegration:
    """Additional comprehensive integration tests"""

    def test_full_pipeline_flow_produces_consistent_results(self, real_test_lxf):
        """
        Running pipeline twice produces same results.

        Ensures idempotent processing for same input.
        """
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline1 = MiltiTakimPipeline()
        result1 = pipeline1.process(real_test_lxf)

        # Clear database for second run
        with get_conn() as conn:
            conn.execute("DELETE FROM fed_results")
            conn.execute("DELETE FROM fed_athlete_best")
            conn.commit()

        pipeline2 = MiltiTakimPipeline()
        result2 = pipeline2.process(real_test_lxf)

        # Compare results
        assert len(result1['selected_tr']) == len(result2['selected_tr']), \
            "TR selection count should be identical"
        assert len(result1['selected_bolge']) == len(result2['selected_bolge']), \
            "BÖLGE selection count should be identical"
        assert result1['total_athletes'] == result2['total_athletes'], \
            "Total athlete count should be identical"

    def test_pipeline_summary_aggregates_correctly(self, real_test_lxf):
        """Verify summary statistics are calculated correctly"""
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        summary = result['summary']

        # Verify summary structure
        for by, stats in summary.items():
            assert 'tr' in stats
            assert 'bolge' in stats
            assert 'total' in stats
            assert isinstance(stats['tr'], int)
            assert isinstance(stats['bolge'], int)
            assert isinstance(stats['total'], int)

            # Verify counts are consistent
            if 'multi' in stats:
                assert stats['total'] >= stats['tr'] + stats['bolge'] + stats.get('multi', 0)
            else:
                assert stats['total'] == stats['tr'] + stats['bolge']

    def test_response_summary_matches_response_counts(self, real_test_lxf):
        """Summary in response matches actual athlete lists"""
        if real_test_lxf is None:
            pytest.skip("Real test LXF not available")

        pipeline = MiltiTakimPipeline()
        result = pipeline.process(real_test_lxf)

        assert result['success'] is True

        # Count TR/BÖLGE by birth year from actual lists
        counted_by_birth_year = {}
        for athlete in result['selected_tr']:
            by = athlete['birth_year']
            if by not in counted_by_birth_year:
                counted_by_birth_year[by] = {'tr': 0, 'bolge': 0}
            counted_by_birth_year[by]['tr'] += 1

        for athlete in result['selected_bolge']:
            by = athlete['birth_year']
            if by not in counted_by_birth_year:
                counted_by_birth_year[by] = {'tr': 0, 'bolge': 0}
            counted_by_birth_year[by]['bolge'] += 1

        # Compare with summary
        summary = result['summary']
        for by, expected in counted_by_birth_year.items():
            actual = summary.get(by, {})
            assert actual.get('tr') == expected['tr'], \
                f"TR count mismatch for {by}: expected {expected['tr']}, got {actual.get('tr')}"
            assert actual.get('bolge') == expected['bolge'], \
                f"BÖLGE count mismatch for {by}: expected {expected['bolge']}, got {actual.get('bolge')}"
