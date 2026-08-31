#!/usr/bin/env python3
"""
Test and analyze LXF data
"""

from modules.lxf_parser import parse_lxf_file, get_birth_year, map_stroke_name
from collections import defaultdict
import sys

def main():
    lxf_file = r"C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\antalya_millitakim_secme_sonuc.lxf"

    print("=" * 60)
    print("LXF VERİ ANALİZİ - Antalya Milli Takım Seçme")
    print("=" * 60)

    try:
        # Parse file
        athletes, results = parse_lxf_file(lxf_file)

        print(f"\n[1] TEMEL İSTATİSTİKLER")
        print(f"  Toplam Sporcu: {len(athletes)}")
        print(f"  Toplam Sonuç: {len(results)}")

        # Birth year analysis
        birth_years = defaultdict(int)
        for athlete in athletes:
            birth_year = get_birth_year(athlete['birthdate'])
            if birth_year:
                birth_years[birth_year] += 1

        print(f"\n[2] YAŞ GRUBU DAĞ ILIMI")
        for year in sorted(birth_years.keys(), reverse=True):
            count = birth_years[year]
            print(f"  {year} (yaş {2026-year}): {count} sporcu")

        # Gender analysis
        genders = defaultdict(int)
        for athlete in athletes:
            gender = athlete['gender']
            genders[gender] += 1

        print(f"\n[3] CİNSİYET DAĞ ILIMI")
        for gender, count in genders.items():
            label = "Erkek" if gender == "M" else "Kadın" if gender == "F" else gender
            print(f"  {label}: {count} sporcu")

        # Club analysis
        clubs = defaultdict(int)
        for athlete in athletes:
            club = athlete.get('club_name', 'Bilinmiyor')
            clubs[club] += 1

        print(f"\n[4] KULÜP DAĞ ILIMI (İlk 10)")
        for club, count in sorted(clubs.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {club}: {count} sporcu")

        # Stroke analysis
        strokes = defaultdict(int)
        for result in results:
            stroke = result.get('stroke')
            if stroke:
                strokes[stroke] += 1

        print(f"\n[5] BRANŞ DAĞ ILIMI")
        for stroke, count in sorted(strokes.items(), key=lambda x: x[1], reverse=True):
            turkish = map_stroke_name(stroke)
            print(f"  {stroke} ({turkish}): {count} sonuç")

        # Distance analysis
        distances = defaultdict(int)
        for result in results:
            distance = result.get('distance')
            if distance:
                distances[int(distance)] += 1

        print(f"\n[6] MESAFELERİ DAĞ ILIMI")
        for distance in sorted(distances.keys()):
            count = distances[distance]
            print(f"  {distance}m: {count} sonuç")

        # Sample results
        print(f"\n[7] ÖRNEK SONUÇLAR (İlk 5)")
        for i, result in enumerate(results[:5], 1):
            athlete = next((a for a in athletes if a['athlete_id'] == result['athlete_id']), None)
            if athlete:
                print(f"  {i}. {athlete['firstname']} {athlete['lastname']}")
                print(f"     {result['distance']}m {map_stroke_name(result['stroke'])}")
                print(f"     Zaman: {result['time_text']} ({result['time_seconds']}s)")

        print("\n" + "=" * 60)
        print("ANALYSE TAMAMLANDI - Veri Hazır!")
        print("=" * 60)

    except Exception as e:
        print(f"HATA: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
