#!/usr/bin/env python3
"""Audit supplied sidereal D1 longitudes. No ephemeris or prediction engine."""
import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import sys

PLANETS = ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')
RULERS = ('Mars','Venus','Mercury','Moon','Sun','Mercury','Venus','Mars','Jupiter','Saturn','Saturn','Jupiter')
NAKSHATRAS = ('Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha','Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati')
ORDER = ('Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury')
YEARS = dict(zip(ORDER, (7,20,6,10,7,18,16,19,17)))
SETTINGS = ('zodiac','ayanamsha','nodes','houses','d9_variant','karaka_system','dasha_year_days','timezone')


def longitude(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value < 360:
        raise ValueError(f'{label}: expected finite numeric longitude in [0,360)')
    return float(value)


def segment(value):
    # Inputs are interpreted literally, without silently snapping rounded values.
    sign = int(value // 30) + 1
    nak = int(value * 3 / 40)
    quarter = int(value * 3 / 10)
    return {'sign': sign, 'degree_in_sign': round(value % 30, 9),
            'd9_sign': int((value * 9) % 360 // 30) + 1,
            'nakshatra': NAKSHATRAS[nak], 'pada': quarter % 4 + 1}


def whole_house(sign, asc):
    return (sign - asc) % 12 + 1


def terminal_paths(longitudes):
    edges = {p: RULERS[segment(v)['sign']-1] for p,v in longitudes.items()}
    results = {}
    for planet in longitudes:
        path = []
        node = planet
        while node not in path and node in edges:
            path.append(node)
            node = edges[node]
        if node in path:
            cycle = path[path.index(node):]
            results[planet] = {'path': path + [node], 'terminal_cycle': cycle}
        else:
            results[planet] = {'path': path + [node], 'missing_dispositor': node}
    return results


def audit(payload):
    if not isinstance(payload, dict):
        raise ValueError('Input must be a JSON object')
    settings = payload.get('settings', {})
    if not isinstance(settings, dict):
        raise ValueError('settings must be an object')
    if settings.get('zodiac') not in (None, 'sidereal'):
        raise ValueError('This audit only accepts sidereal D1 longitudes; convert using the chosen ephemeris first')
    d1 = payload.get('d1')
    if not isinstance(d1, dict) or not isinstance(d1.get('planets'), dict):
        raise ValueError('d1.planets must be an object')
    asc = longitude(d1.get('asc_longitude'), 'd1.asc_longitude')
    planets = d1['planets']
    if not planets:
        raise ValueError('d1.planets must not be empty')
    unsupported = set(planets) - set(PLANETS)
    if unsupported:
        raise ValueError('Unsupported planet names: ' + ', '.join(sorted(unsupported)))
    lons = {}
    for planet, row in planets.items():
        if not isinstance(row, dict):
            raise ValueError(f'{planet}: row must be an object')
        lons[planet] = longitude(row.get('longitude'), planet)
    warnings = []
    missing = [p for p in PLANETS if p not in lons]
    if missing:
        warnings.append('Missing planets: ' + ', '.join(missing))
    for field in SETTINGS:
        if settings.get(field) is None or settings.get(field) == '':
            warnings.append('Unspecified setting: ' + field)
    whole = settings.get('houses') == 'whole-sign'
    standard_d9 = settings.get('d9_variant') == 'standard-parashari'
    if not whole:
        warnings.append('Whole-sign houses shown for reference only; supplied house values are not checked')
    if not standard_d9:
        warnings.append('Standard D9 shown for reference only; supplied D9 signs are not checked')
    if 'karakas' in payload:
        if not isinstance(payload['karakas'], dict):
            raise ValueError('karakas must be an object')
        for planet, roles in payload['karakas'].items():
            if planet not in PLANETS or not isinstance(roles, list) or any(role not in ('AK','AmK','BK','MK','PiK','PK','GK','DK') for role in roles):
                raise ValueError(f'Invalid supplied karaka roles for {planet}')
    computed = {}
    mismatches = []
    for planet, lon in lons.items():
        result = segment(lon)
        result['whole_sign_house'] = whole_house(result['sign'], segment(asc)['sign'])
        result['source'] = planets[planet].get('source')
        checks = {'sign': result['sign'], 'nakshatra': result['nakshatra'], 'pada': result['pada']}
        if whole:
            checks['house'] = result['whole_sign_house']
        if standard_d9:
            checks['d9_sign'] = result['d9_sign']
        for key, actual in checks.items():
            if key in planets[planet]:
                supplied = planets[planet][key]
                if (key != 'nakshatra' and (isinstance(supplied, bool) or not isinstance(supplied, int))) or supplied != actual:
                    mismatches.append({'planet': planet, 'field': key, 'supplied': supplied, 'computed': actual})
        computed[planet] = result
    if 'Rahu' in lons and 'Ketu' in lons:
        error = abs((lons['Rahu']-lons['Ketu']) % 360 - 180)
        if error > 0.02:
            mismatches.append({'field':'node_opposition','error_degrees':round(error,9), 'tolerance_degrees':0.02})
    return {'scope':'Supplied-coordinate mathematical audit only; no birth ephemeris, strength calculation, karaka reassignment or prediction',
            'settings':settings, 'ascendant':segment(asc), 'computed':computed,
            'supplied_karakas_unverified':payload.get('karakas',{}),
            'dispositor_paths':terminal_paths(lons), 'warnings':warnings,
            'mismatches':mismatches, 'status':'mismatch' if mismatches else ('incomplete' if warnings else 'consistent')}


def split_period(start, end, lord):
    """Split a COMPLETE parent period, never a truncated birth balance."""
    if lord not in ORDER:
        raise ValueError('lord must be one of: '+', '.join(ORDER))
    start = datetime.fromisoformat(start)
    end = datetime.fromisoformat(end)
    if start.utcoffset() is None or end.utcoffset() is None:
        raise ValueError('Both boundaries need explicit UTC offsets')
    if end <= start:
        raise ValueError('end must be after start')
    seconds = (end-start).total_seconds()
    idx = ORDER.index(lord)
    elapsed = 0
    rows = []
    for offset in range(9):
        sub = ORDER[(idx+offset) % 9]
        begin = start + timedelta(seconds=seconds*elapsed/120)
        elapsed += YEARS[sub]
        finish = end if offset == 8 else start+timedelta(seconds=seconds*elapsed/120)
        rows.append({'lord':sub, 'start':begin.isoformat(), 'end':finish.isoformat(), 'fraction':f'{YEARS[sub]}/120'})
    return {'scope':'Proportional subdivisions of the supplied complete parent period; verify software conventions and rounding', 'parent_lord':lord, 'periods':rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--split-start')
    parser.add_argument('--split-end')
    parser.add_argument('--lord', choices=ORDER)
    args=parser.parse_args()
    try:
        split_values = (args.split_start,args.split_end,args.lord)
        if any(split_values):
            if not all(split_values) or args.input:
                raise ValueError('Use all three split options without an input file')
            result=split_period(*split_values)
        else:
            if args.input is None:
                raise ValueError('Provide an input JSON file or all three split options')
            result=audit(json.loads(args.input.read_text(encoding='utf-8')))
        output=json.dumps(result, ensure_ascii=False, indent=2)+'\n'
        if args.output:
            args.output.write_text(output,encoding='utf-8')
        else:
            sys.stdout.write(output)
        return 1 if result.get('mismatches') else 0
    except (ValueError, TypeError, OSError, OverflowError) as error:
        print(json.dumps({'error':str(error)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
