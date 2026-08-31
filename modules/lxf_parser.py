"""
LXF (Lenex) format parser for swimming competition data
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime
from modules.m4_mapping import lookup_club


def parse_lxf_file(file_path: str) -> tuple[List[Dict], List[Dict]]:
    """
    Parse LXF file and extract athletes and results.

    Returns:
        Tuple of (athletes, results) lists
    """
    athletes_list = []
    results_list = []

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            xml_files = [f for f in zip_ref.namelist() if f.endswith(('.xml', '.lef'))]

            if not xml_files:
                raise ValueError(f"No XML files found in {file_path}")

            with zip_ref.open(xml_files[0]) as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Build event lookup table (eventid -> event info)
                events_lookup = {}
                events = root.findall('.//EVENT')
                for event in events:
                    event_id = event.get('eventid')
                    swim_style = event.find('.//SWIMSTYLE')
                    distance = None
                    stroke = None

                    if swim_style is not None:
                        distance = swim_style.get('distance')
                        stroke = swim_style.get('stroke')

                    events_lookup[event_id] = {
                        'distance': distance,
                        'stroke': stroke,
                        'gender': event.get('gender'),
                    }

                # Build club lookup table (athleteid -> club info)
                # Handles LXF formats where athletes are nested inside CLUB elements
                club_by_athlete = {}
                clubs = root.findall('.//CLUB')
                for club_elem in clubs:
                    club_id = club_elem.get('clubid')
                    club_name = club_elem.get('clubname') or club_elem.get('name')
                    athletes_in_club = club_elem.findall('.//ATHLETE')
                    for athlete_in_club in athletes_in_club:
                        athlete_id = athlete_in_club.get('athleteid')
                        if athlete_id and club_name:
                            club_by_athlete[athlete_id] = {
                                'club_id': club_id,
                                'club_name': club_name,
                            }

                # Parse athletes
                athlete_elements = root.findall('.//ATHLETE')

                for athlete_elem in athlete_elements:
                    athlete_id = athlete_elem.get('athleteid')
                    athlete = {
                        'athlete_id': athlete_id,
                        'firstname': athlete_elem.get('firstname'),
                        'lastname': athlete_elem.get('lastname'),
                        'birthdate': athlete_elem.get('birthdate'),
                        'gender': athlete_elem.get('gender'),
                        'license': athlete_elem.get('license'),
                        'club_id': None,
                        'club_name': None,
                        'city': 'Unknown',
                        'region': 0,
                    }

                    # Get club info if available (direct child CLUB element)
                    club_elem = athlete_elem.find('.//CLUB')
                    if club_elem is not None:
                        athlete['club_id'] = club_elem.get('clubid')
                        athlete['club_name'] = club_elem.get('clubname')
                    # Or from parent CLUB element (some LXF formats)
                    elif athlete_id in club_by_athlete:
                        athlete['club_id'] = club_by_athlete[athlete_id]['club_id']
                        athlete['club_name'] = club_by_athlete[athlete_id]['club_name']

                    # Look up city/region from Excel mapping
                    if athlete['club_name']:
                        mapping = lookup_club(athlete['club_name'])
                        if mapping:
                            athlete['city'] = mapping['city']
                            athlete['region'] = mapping['region']

                    athletes_list.append(athlete)

                    # Parse results for this athlete
                    results_elem = athlete_elem.find('.//RESULTS')
                    if results_elem is not None:
                        for result_elem in results_elem.findall('.//RESULT'):
                            event_id = result_elem.get('eventid')
                            event_info = events_lookup.get(event_id, {})

                            result = {
                                'athlete_id': athlete_id,
                                'event_id': event_id,
                                'distance': event_info.get('distance'),
                                'stroke': event_info.get('stroke'),
                                'time_text': result_elem.get('swimtime'),
                                'time_seconds': parse_swimtime(result_elem.get('swimtime')),
                                'place': result_elem.get('place'),
                                'points': result_elem.get('points'),
                            }

                            results_list.append(result)

        return athletes_list, results_list

    except Exception as e:
        raise RuntimeError(f"Failed to parse LXF file: {e}")


def parse_swimtime(time_text: Optional[str]) -> Optional[float]:
    """Convert swim time string (MM:SS.XX format) to seconds."""
    if not time_text or time_text == '00:00:00.00':
        return None

    try:
        parts = time_text.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError):
        pass

    return None


def get_birth_year(birthdate_str: Optional[str]) -> Optional[int]:
    """Extract birth year from birthdate string (YYYY-MM-DD format)."""
    if not birthdate_str:
        return None

    try:
        # Handle YYYY-MM-DD format
        if '-' in birthdate_str:
            year = int(birthdate_str.split('-')[0])
            return year
        # Handle other formats
        return int(birthdate_str[:4])
    except (ValueError, IndexError):
        return None


def map_stroke_name(stroke_code: Optional[str]) -> Optional[str]:
    """Map stroke code to Turkish name."""
    stroke_map = {
        'FREE': 'Serbest',
        '1': 'Serbest',
        'BACK': 'Sırtüstü',
        '2': 'Sırtüstü',
        'BREAST': 'Kurbağalama',
        '3': 'Kurbağalama',
        'FLY': 'Kelebek',
        '4': 'Kelebek',
        'MEDLEY': 'Karışık',
        '5': 'Karışık',
    }
    return stroke_map.get(stroke_code)
