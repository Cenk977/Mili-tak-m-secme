"""
federasyon/pipeline.py
----------------------
MiltiTakimPipeline: Orchestration class for end-to-end LXF → scoring → ranking → DB.

Flow:
  1. parse_and_extract()  — LXF → athletes + results
  2. score_athletes()     — athletes + results → event_scores
  3. rank_athletes()      — event_scores → selection decisions
  4. save_to_database()   — persistence
  5. return_response()    — aggregated response dict
"""

import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

from modules.lxf_parser import parse_lxf_file as parse, get_birth_year
from federasyon.scorer import (
    score_athlete_row,
    score_event,
    parse_time,
    best_scores_sequence,
    compute_ranking_key,
)
from federasyon.ranker import rank_all
from federasyon.db_fed import (
    upsert_fed_results,
    update_athlete_selection,
    get_selected_athletes,
    migrate_add_selection_columns
)
from federasyon.scoring_tables import SELECTION_QUOTAS

logger = logging.getLogger(__name__)

_SCHEMA_READY = False


def ensure_schema():
    """
    Run the fed_* schema migration once per process.

    The server calls migrate_add_selection_columns() at startup; this guard
    keeps stand-alone/library use (and tests) working without re-running the
    migration on every pipeline instantiation.
    """
    global _SCHEMA_READY
    if not _SCHEMA_READY:
        migrate_add_selection_columns()
        _SCHEMA_READY = True


class MiltiTakimPipeline:
    """
    Orchestrates the complete pipeline from LXF file to selection decisions.

    Process:
      1. Parse LXF file
      2. Score each athlete's events
      3. Rank all athletes
      4. Save results and selection decisions to database
      5. Return aggregated response
    """

    def __init__(self):
        """Initialize the pipeline (schema migration happens lazily in process())."""
        logger.info("MiltiTakimPipeline initialized")

    def process(self, lxf_path: str) -> Dict[str, Any]:
        """
        Main orchestration method.

        Args:
            lxf_path: Path to LXF file

        Returns:
            Dict with keys:
              - success: bool
              - message: str
              - selected_tr: list[dict]  # [{name, birth_year, selected_slot, top3_total}, ...]
              - selected_bolge: list[dict]
              - baraj_yok_count: int
              - total_athletes: int
              - summary: dict  # {birth_year: {tr, bolge, total}, ...}
        """
        try:
            ensure_schema()

            # Step 1: Parse LXF
            logger.info(f"Parsing LXF: {lxf_path}")
            athletes, results = self.parse_and_extract(lxf_path)
            logger.info(f"Parsed {len(athletes)} athletes, {len(results)} results")

            # Step 2: Score athletes — event_scores are built from the parsed
            # swim results, NOT from Excel-style columns on the athlete dict.
            logger.info("Scoring athletes...")
            athletes = self.score_athletes(athletes, results)
            scored_count = sum(1 for a in athletes if a.get('event_scores'))
            logger.info(f"Scored {scored_count}/{len(athletes)} athletes")

            # Step 3: Rank athletes
            logger.info("Ranking athletes...")
            ranked = self.rank_athletes(athletes)
            logger.info(f"Ranked {len(ranked)} athletes")

            # Step 3b: Validate quota enforcement at runtime
            self.validate_results(ranked)

            # Step 4: Save to database
            logger.info("Saving to database...")
            self.save_to_database(ranked)
            logger.info(f"Saved to database")

            # Step 5: Build response
            response = self.build_response(ranked)
            response['success'] = True
            response['message'] = f"Successfully processed {response['total_athletes']} athletes"

            logger.info(f"Pipeline completed successfully")
            return response

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return {
                'success': False,
                'message': f"File not found: {lxf_path}",
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Pipeline error: {str(e)}",
                'error': str(e)
            }

    def parse_and_extract(self, lxf_path: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse LXF file and extract athletes + results.
        Normalizes athlete data: converts birthdate → birth_year, renames fields.

        Args:
            lxf_path: Path to LXF file

        Returns:
            Tuple of (athletes_list, results_list)
        """
        try:
            athletes, results = parse(lxf_path)

            # Normalize athlete data
            for athlete in athletes:
                # Convert birthdate to birth_year
                if 'birthdate' in athlete and 'birth_year' not in athlete:
                    athlete['birth_year'] = get_birth_year(athlete.get('birthdate'))

                # Map athlete_id to name for pipeline compatibility
                if 'name' not in athlete:
                    firstname = athlete.get('firstname', '')
                    lastname = athlete.get('lastname', '')
                    athlete['name'] = f"{firstname} {lastname}".strip() or 'Unknown'

                # Map club_name to club
                if 'club' not in athlete and 'club_name' in athlete:
                    athlete['club'] = athlete['club_name']

            logger.debug(f"Extracted {len(athletes)} athletes, {len(results)} results")
            return athletes, results
        except Exception as e:
            logger.error(f"Parse error: {e}")
            raise

    @staticmethod
    def _index_results(results: List[Dict]) -> Dict[str, List[Dict]]:
        """Group parsed LXF results by athlete_id."""
        by_athlete: Dict[str, List[Dict]] = {}
        for result in results or []:
            athlete_id = result.get('athlete_id')
            if athlete_id is None:
                continue
            by_athlete.setdefault(str(athlete_id), []).append(result)
        return by_athlete

    @staticmethod
    def _score_from_results(athlete_results: List[Dict], birth_year: int,
                            gender: str) -> Tuple[Dict[tuple, int], Dict[tuple, Dict]]:
        """
        Map a list of LXF result dicts → ({(stroke, distance): points},
                                          {(stroke, distance): {time_seconds, time_text}}).

        Only positive scores are kept. If the same event appears more than once
        (heat + final), the best (highest) score / fastest time wins.
        """
        event_scores: Dict[tuple, int] = {}
        event_times: Dict[tuple, Dict] = {}

        for result in athlete_results:
            stroke = result.get('stroke')
            raw_distance = result.get('distance')
            if not stroke or raw_distance in (None, ''):
                continue
            try:
                distance = int(raw_distance)
            except (TypeError, ValueError):
                continue

            time_seconds = result.get('time_seconds')
            if time_seconds is None:
                time_seconds = parse_time(result.get('time_text'))
            if time_seconds is None or time_seconds <= 0:
                continue

            event = (stroke, distance)
            points = score_event(time_seconds, birth_year, gender, stroke, distance)

            prev_time = event_times.get(event, {}).get('time_seconds')
            if prev_time is None or time_seconds < prev_time:
                event_times[event] = {
                    'time_seconds': time_seconds,
                    'time_text': result.get('time_text'),
                }

            if points > 0 and points > event_scores.get(event, 0):
                event_scores[event] = points

        return event_scores, event_times

    def score_athletes(self, athletes: List[Dict],
                       results: List[Dict] = None) -> List[Dict]:
        """
        Score each athlete's events using birth_year and gender.

        The primary source of truth is the parsed `results` list (swim times),
        keyed to athletes by athlete_id. Excel-style columns on the athlete dict
        (Serbest_50m, ...) are only used as a fallback when no results exist for
        that athlete — this keeps spreadsheet-sourced input working.

        Args:
            athletes: List of athlete dicts
            results:  List of parsed result dicts from the LXF parser

        Returns:
            Same list, with 'event_scores' / 'event_times' / 'top3_total' added
        """
        results_by_athlete = self._index_results(results)

        for athlete in athletes:
            birth_year = athlete.get('birth_year')
            gender = athlete.get('gender', '')
            athlete.setdefault('event_times', {})

            if not birth_year:
                logger.warning(f"Athlete {athlete.get('name')} missing birth_year, skipping scoring")
                athlete['event_scores'] = {}
                athlete['top3_total'] = 0
                continue

            athlete_results = results_by_athlete.get(str(athlete.get('athlete_id')), [])

            try:
                if athlete_results:
                    event_scores, event_times = self._score_from_results(
                        athlete_results, birth_year, gender
                    )
                    athlete['event_times'] = event_times
                else:
                    # Fallback: Excel-style columns (Serbest_50m, ...)
                    event_scores = score_athlete_row(athlete, birth_year, gender)

                athlete['event_scores'] = event_scores
                athlete['top3_total'] = (
                    sum(best_scores_sequence(event_scores)[:3]) if event_scores else 0
                )

            except (KeyError, TypeError, ValueError) as e:
                logger.warning(f"Scoring error for {athlete.get('name')}: {e}")
                athlete['event_scores'] = {}
                athlete['top3_total'] = 0

        return athletes

    def rank_athletes(self, athletes: List[Dict]) -> List[Dict]:
        """
        Rank athletes using federasyon/ranker.rank_all().

        Args:
            athletes: List of athletes with event_scores

        Returns:
            Ranked list with selection decisions
        """
        try:
            ranked = rank_all(athletes)

            # Ensure all athletes have required fields
            for athlete in ranked:
                if 'selected' not in athlete:
                    athlete['selected'] = '-'
                if 'selected_slot' not in athlete:
                    athlete['selected_slot'] = '-'
                if 'ranking_key' not in athlete:
                    athlete['ranking_key'] = str(())
                if 'tied' not in athlete:
                    athlete['tied'] = False
                if 'top3_total' not in athlete:
                    athlete['top3_total'] = 0

            return ranked
        except Exception as e:
            logger.error(f"Ranking error: {e}")
            raise

    def save_to_database(self, ranked_athletes: List[Dict]) -> None:
        """
        Save ranked athletes to database.
        Calls upsert_fed_results() and update_athlete_selection() for each athlete.

        Args:
            ranked_athletes: List of ranked athletes with selection info
        """
        try:
            for athlete in ranked_athletes:
                # Ensure athlete has all required fields
                athlete.setdefault('event_scores', {})
                athlete.setdefault('selected', '-')
                athlete.setdefault('selected_slot', '-')
                athlete.setdefault('ranking_key', '')
                athlete.setdefault('tied', False)

                # Save raw results (one row per event)
                if athlete['event_scores']:
                    upsert_fed_results(athlete, race_leg='milli_takim')

                # Update selection status
                update_athlete_selection(athlete)

            logger.info(f"Saved {len(ranked_athletes)} athletes to database")
        except Exception as e:
            logger.error(f"Database save error: {e}")
            raise

    def build_response(self, ranked_athletes: List[Dict]) -> Dict[str, Any]:
        """
        Build response dict for client.

        Args:
            ranked_athletes: List of ranked athletes

        Returns:
            Response dict with selected_tr, selected_bolge, baraj_yok_count, summary
        """
        selected_tr = []
        selected_bolge = []
        baraj_yok_count = 0

        # Group by birth_year for summary
        summary_by_birth_year = {}

        for athlete in ranked_athletes:
            birth_year = athlete.get('birth_year')

            # Initialize summary for this birth year
            if birth_year not in summary_by_birth_year:
                summary_by_birth_year[birth_year] = {
                    'birth_year': birth_year,
                    'multi': 0,
                    'tr': 0,
                    'bolge': 0,
                    'total': 0
                }

            selected = athlete.get('selected', '-')

            if selected == 'TR':
                selected_tr.append({
                    'name': athlete.get('name', ''),
                    'birth_year': birth_year,
                    'gender': athlete.get('gender', ''),
                    'selected_slot': athlete.get('selected_slot', ''),
                    'top3_total': athlete.get('top3_total', 0),
                    'tied': bool(athlete.get('tied', False)),
                    'region': athlete.get('region'),
                    'city': athlete.get('city', ''),
                    'club': athlete.get('club', '')
                })
                summary_by_birth_year[birth_year]['tr'] += 1
                summary_by_birth_year[birth_year]['total'] += 1

            elif selected == 'BÖLGE':
                selected_bolge.append({
                    'name': athlete.get('name', ''),
                    'birth_year': birth_year,
                    'gender': athlete.get('gender', ''),
                    'selected_slot': athlete.get('selected_slot', ''),
                    'top3_total': athlete.get('top3_total', 0),
                    'tied': bool(athlete.get('tied', False)),
                    'region': athlete.get('region'),
                    'city': athlete.get('city', ''),
                    'club': athlete.get('club', '')
                })
                summary_by_birth_year[birth_year]['bolge'] += 1
                summary_by_birth_year[birth_year]['total'] += 1

            elif selected == 'BARAJ_YOK':
                baraj_yok_count += 1

            elif selected == 'MULTINATIONS':
                summary_by_birth_year[birth_year]['multi'] += 1
                summary_by_birth_year[birth_year]['total'] += 1

        return {
            'selected_tr': selected_tr,
            'selected_bolge': selected_bolge,
            'baraj_yok_count': baraj_yok_count,
            'total_athletes': len(ranked_athletes),
            'summary': summary_by_birth_year
        }

    def validate_results(self, athletes: List[Dict]) -> bool:
        """
        Validate that selection results respect quotas and consistency rules.

        Args:
            athletes: List of ranked athletes with selection info

        Returns:
            True if valid, raises Exception otherwise
        """
        # Group by (birth_year, gender) — the ranker applies quotas per
        # birth-year AND gender group, so validation must use the same key.
        by_group = {}
        for athlete in athletes:
            key = (athlete.get('birth_year'), athlete.get('gender'))
            by_group.setdefault(key, []).append(athlete)

        # Check TR quotas (ties at the quota boundary may legitimately add rows)
        for (by, gender), athletes_list in by_group.items():
            tr_selected = [a for a in athletes_list if a.get('selected') == 'TR']

            if by in SELECTION_QUOTAS:
                quota = SELECTION_QUOTAS[by]['tr']
                tied_extra = sum(1 for a in tr_selected if a.get('tied'))
                if len(tr_selected) > quota + tied_extra:
                    raise Exception(
                        f"TR quota exceeded for {by}/{gender}: "
                        f"{len(tr_selected)} > {quota}"
                    )

        # Check selection status validity
        valid_statuses = {'-', 'TR', 'BÖLGE', 'BARAJ_YOK', 'MULTINATIONS'}
        for athlete in athletes:
            selected = athlete.get('selected', '-')
            if selected not in valid_statuses:
                raise Exception(f"Invalid selection status for {athlete.get('name')}: {selected}")

        return True
