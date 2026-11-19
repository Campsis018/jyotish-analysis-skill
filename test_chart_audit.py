import copy
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/analyze-jyotish'
SCRIPT = SKILL / 'scripts/chart_audit.py'
spec = importlib.util.spec_from_file_location('chart_audit', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AuditTests(unittest.TestCase):
    def fixture(self):
        return json.loads((SKILL/'assets/synthetic-chart.json').read_text())

    def test_fixture(self):
        r=m.audit(self.fixture())
        self.assertEqual(r['status'],'consistent')
        self.assertEqual(r['computed']['Sun']['d9_sign'],2)
        self.assertEqual(r['computed']['Moon']['pada'],1)

    def test_sign_nakshatra_d9_boundaries(self):
        for lon,sign,d9,nak,pada in [(0,1,1,'Ashwini',1),(10/3,1,2,'Ashwini',2),(40/3,1,5,'Bharani',1),(30,2,10,'Krittika',2),(120,5,1,'Magha',1),(360-1e-7,12,12,'Revati',4)]:
            r=m.segment(lon)
            self.assertEqual((r['sign'],r['d9_sign'],r['nakshatra'],r['pada']),(sign,d9,nak,pada))

    def test_wrap_whole_house(self):
        self.assertEqual(m.whole_house(1,12),2)
        self.assertEqual(m.whole_house(12,1),12)

    def test_invalid_longitudes(self):
        for value in (None,True,False,'15',-1,360,float('nan'),float('inf')):
            with self.subTest(value=value),self.assertRaises(ValueError):
                m.longitude(value,'test')

    def test_tropical_rejected(self):
        d=self.fixture();d['settings']['zodiac']='tropical'
        with self.assertRaises(ValueError):m.audit(d)

    def test_mismatch(self):
        d=self.fixture();d['d1']['planets']['Sun']['house']=4
        self.assertEqual(m.audit(d)['mismatches'][0]['field'],'house')

    def test_bhava_not_compared_as_whole_sign(self):
        d=self.fixture();d['settings']['houses']='bhava-chalit';d['d1']['planets']['Sun']['house']=4
        r=m.audit(d)
        self.assertEqual(r['mismatches'],[])
        self.assertEqual(r['status'],'incomplete')

    def test_nonstandard_d9_not_overridden(self):
        d=self.fixture();d['settings']['d9_variant']='other';d['d1']['planets']['Sun']['d9_sign']=1
        self.assertEqual(m.audit(d)['mismatches'],[])

    def test_node_axis(self):
        d=self.fixture();d['d1']['planets']['Ketu']['longitude']=349
        self.assertEqual(m.audit(d)['mismatches'][0]['field'],'node_opposition')

    def test_roles_preserved(self):
        d=self.fixture();d['karakas']={'Mercury':['AmK','GK'],'Venus':[]}
        self.assertEqual(m.audit(d)['supplied_karakas_unverified'],d['karakas'])

    def test_multiple_dispositor_terminals(self):
        r=m.terminal_paths({'Sun':125,'Moon':95,'Venus':135})
        self.assertEqual(r['Sun']['terminal_cycle'],['Sun'])
        self.assertEqual(r['Moon']['terminal_cycle'],['Moon'])
        self.assertEqual(r['Venus']['terminal_cycle'],['Sun'])

    def test_dispositor_loop(self):
        r=m.terminal_paths({'Mars':35,'Venus':5})
        self.assertEqual(set(r['Mars']['terminal_cycle']),{'Mars','Venus'})

    def test_split_continuity_and_fraction(self):
        r=m.split_period('2030-01-01T00:00:00+00:00','2031-01-01T00:00:00+00:00','Jupiter')['periods']
        self.assertEqual(len(r),9)
        self.assertEqual(r[0]['lord'],'Jupiter')
        self.assertEqual(r[-1]['lord'],'Rahu')
        self.assertEqual(r[0]['start'],'2030-01-01T00:00:00+00:00')
        self.assertEqual(r[-1]['end'],'2031-01-01T00:00:00+00:00')
        for a,b in zip(r,r[1:]):self.assertEqual(a['end'],b['start'])
        seconds=(datetime.fromisoformat(r[0]['end'])-datetime.fromisoformat(r[0]['start'])).total_seconds()
        self.assertAlmostEqual(seconds,365*86400*16/120,places=5)

    def test_invalid_periods(self):
        for args in [('2030-01-01','2031-01-01','Jupiter'),('2031-01-01T00:00:00+00:00','2030-01-01T00:00:00+00:00','Jupiter')]:
            with self.assertRaises(ValueError):m.split_period(*args)

    def test_cli_error_codes(self):
        r=subprocess.run([sys.executable,str(SCRIPT),str(SKILL/'assets/input-template.json')],capture_output=True,text=True)
        self.assertEqual(r.returncode,2)
        self.assertIn('error',json.loads(r.stderr))
        r=subprocess.run([sys.executable,str(SCRIPT),str(SKILL/'assets/synthetic-chart.json')],capture_output=True,text=True)
        self.assertEqual(r.returncode,0)
        self.assertEqual(json.loads(r.stdout)['status'],'consistent')

    def test_markdown_local_links_resolve(self):
        for p in SKILL.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
                if not target.startswith(('http:','https:','#')):
                    self.assertTrue((p.parent/target.split('#')[0]).exists(),(p,target))


if __name__=='__main__':unittest.main()
