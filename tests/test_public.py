"""Public reproduction tests; mutations are memory-only, not demonstration data."""
import copy
import hashlib
import subprocess
import sys
import unittest
from pipeline import compiler as c
from pipeline.build_local import IDS, build, compile_public, protected_semantics, validate_publication

class PublicReleaseTests(unittest.TestCase):
    def data(self, pid): return c.load_json(c.ROOT / f'data/public_inputs/{pid}.json')

    def test_five_frozen_semantic_digests(self):
        frozen = c.load_json(c.ROOT/'publication/semantic-baseline.json')
        for pid in IDS: self.assertEqual(protected_semantics(compile_public(pid)), frozen[pid])

    def test_candidate_excluded_isolation(self):
        for pid in IDS:
            s=compile_public(pid)['semantic'];blocked={o['id'] for r in s['evidence']['candidates'] for o in r['observations']} | {r['observation']['id'] for r in s['evidence']['excluded']}
            self.assertFalse(blocked & {oid for f in s['findings'] for oid in f['observation_refs']})
            if pid in ('C09','C12'):
                self.assertEqual(len(s['evidence']['accepted']),1)
                self.assertTrue(all(r['identity_state']=='POSSIBLE_MATCH' for r in s['evidence']['candidates']))
        self.assertEqual(len(compile_public('C12')['semantic']['evidence']['excluded']),2)

    def test_completion_grounding_and_states(self):
        for pid in IDS:
            s=compile_public(pid)['semantic'];f=next(f for f in s['findings'] if f['id']=='completion');a=next(a for a in s['answers'] if a['question_id']=='completed')
            admitted={o['id']:o for r in s['evidence']['accepted'] for o in r['observations']}
            self.assertEqual((f['proposition'],f['evidence_state']),('The project was completed.','UNVERIFIABLE'))
            self.assertTrue(all(admitted[oid]['kind']=='reported_percent_complete' for oid in f['observation_refs']))
            self.assertEqual('Historical reported progress' in a['clauses'][0]['text'],bool(f['observation_refs']))
            self.assertEqual(a['clauses'][0]['finding_refs'],['completion'])
            self.assertEqual(f['coverage_refs'],[s['coverage']['id']])

    def test_financial_types_and_historical_qualification(self):
        for pid in IDS:
            s=compile_public(pid)['semantic']
            self.assertEqual(next(x for x in s['stages'] if x['dimension']=='payment')['evidence_state'],'UNVERIFIABLE')
            for r in s['evidence']['accepted']:
                for o in r['observations']:
                    if o['kind']=='amount_certified':
                        f=next(f for f in s['findings'] if f['id']=='observation:'+o['id'])
                        self.assertIn('not independently verified treasury payment',f['qualification'])
                    if o['kind']=='reported_percent_complete': self.assertIsNone(o['observation_date'])

    def test_historical_100_percent_still_refuses_completion(self):
        d=self.data('C01')
        for r in d['records']:
            for o in r['observations']:
                if o['kind']=='reported_percent_complete':
                    o['value']='100';o['raw_value']='100%'
        records={r['id']:r for r in d['records']}
        for r in records.values():r['review']['content_sha256']=c.record_digest(r)
        for decision in d['identity_decisions']:
            decision['record_sha256']=c.record_digest(records[decision['record_id']])
            decision['anchor_sha256']=c.record_digest(records[decision['anchor_record_id']])
        s=c.compile_evidence(d,release=True)['semantic']
        f=next(f for f in s['findings'] if f['id']=='completion')
        a=next(a for a in s['answers'] if a['question_id']=='completed')
        self.assertEqual(f['evidence_state'],'UNVERIFIABLE')
        self.assertIn('does not establish',a['clauses'][0]['text'])
        self.assertEqual(a['clauses'][0]['finding_refs'],['completion'])

    def test_publication_missing_pending_changed_and_unknown_units_fail(self):
        d=self.data('C12');reg=c.load_json(c.ROOT/'publication/register.json');key=next(iter(reg['units']['C12']))
        for change in ('remove','pending','value','category'):
            r=copy.deepcopy(reg);x=copy.deepcopy(d)
            if change=='remove':del r['units']['C12'][key]
            if change=='pending':r['units']['C12'][key]['disposition']='PENDING'
            if change=='value':x['project']['title']+=' altered'
            if change=='category':r['units']['C12'][key]['category']='unreviewed'
            with self.assertRaises(c.EvidenceError):validate_publication('C12',x,r)

    def test_unsafe_urls_and_missing_provenance_fail(self):
        for kind in ('url','hash','locator'):
            d=self.data('C01')
            if kind=='url':d['sources'][0]['url']='javascript:alert(1)'
            if kind=='hash':d['records'][0]['document_sha256']='0'*64
            if kind=='locator':del d['records'][0]['locator']
            with self.assertRaises(c.EvidenceError):c.compile_evidence(d,release=True)

    def test_tamper_and_stale_release_artifact_fail(self):
        for pid in IDS:
            d=self.data(pid);a=compile_public(pid);a['semantic']['answers'][2]['clauses'][0]['text']='Completed.';a['semantic_sha256']=c.digest(a['semantic'])
            with self.assertRaises(c.EvidenceError):c.verify_artifact(a,d,release=True)

    def test_all_fixed_references_resolve(self):
        for pid in IDS:
            s=compile_public(pid)['semantic'];ids={f['id'] for f in s['findings']}
            self.assertEqual({a['question_id'] for a in s['answers']},{'known','payment','completed'})
            for a in s['answers']:
                for clause in a['clauses']:self.assertTrue(set(clause['finding_refs'])<=ids)

    def test_index_uses_only_accepted_terms(self):
        index=c.load_json(c.ROOT/'data/artifacts/index.json')
        for row in index['projects']:
            s=compile_public(row['id'])['semantic'];terms={o['value'] for r in s['evidence']['accepted'] for o in r['observations'] if o['kind'] in ('route','agency','location','contract_number','project_code')}
            self.assertEqual(set(row['terms']),terms)

    def test_separate_process_generation_and_copy_parity(self):
        first={pid:(c.ROOT/f'data/artifacts/{pid}.json').read_bytes() for pid in IDS}
        for _ in range(2):
            p=subprocess.run([sys.executable,'-m','pipeline.build_local'],cwd=c.ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            for pid,raw in first.items():
                self.assertEqual((c.ROOT/f'data/artifacts/{pid}.json').read_bytes(),raw)
                self.assertEqual((c.ROOT/f'apps/web/public/data/{pid}.json').read_bytes(),raw)

if __name__=='__main__':unittest.main(verbosity=2)
