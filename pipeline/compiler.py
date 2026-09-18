"""Offline, fail-closed evidence compiler. All source text is inert data."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / 'schemas'
RULES_PATH = Path(__file__).with_name('rules.json')
MONEY = {'annual_appropriation', 'planning_amount', 'tender_value', 'award_value',
         'contract_sum', 'amount_certified', 'transaction_value'}
APPROVED_REUSE = {'APPROVED_FACTUAL_SUBSET', 'APPROVED_EXTRACT'}
DIMENSIONS = ('appropriation', 'procurement', 'award', 'payment', 'implementation')

# These bindings are controlled schema semantics, not source-supplied instructions.
# Relabelling a certified field as a payment observation cannot pass validation.
FIELD_BINDINGS = {
    'appropriation': {
        'CODE': 'project_code', 'LINE ITEM': 'route',
        'LINE ITEM / C/NO.': 'contract_number', 'MDA': 'agency',
        'LINE ITEM / State': 'location', 'AMOUNT': 'annual_appropriation',
    },
    'official_implementation': {
        'Project Title': 'route', 'Project Title / Contact No.': 'contract_number',
        'Project Title / State': 'location', 'Report heading / Ministry': 'agency',
        'Name of Contractor': 'contractor', 'Contract Sum (N:K)': 'contract_sum',
        'Amount Certified To Date (N)': 'amount_certified',
        '% Completion to date': 'reported_percent_complete',
        'Contract Award Date': 'award_date', 'Remarks': 'source_remark',
    },
    'open_contracting': {
        '/ocid': 'procurement_id', '/tender/title': 'route', '/buyer/name': 'agency',
        '/planning/budget/amount/amount': 'planning_amount',
        '/planning/budget/project': 'planning_description',
        '/tender/value/amount': 'tender_value', '/awards/0/value/amount': 'award_value',
        '/contracts/0/value/amount': 'contract_sum',
        '/awards/0/suppliers/0/name': 'contractor', '/awards/0/date': 'award_date',
        '/contracts/0/implementation/transactions/0/value/amount': 'transaction_value',
        '/contracts/0/implementation/transactions/0/payee/id': 'payee_reference',
        '/date': 'record_publication_date',
        **{f'/contracts/0/implementation/milestones/{i}/{field}': kind
           for i in (0, 1) for field, kind in [('description', 'milestone_description'), ('status', 'milestone_status')]},
    },
}


class EvidenceError(ValueError):
    """Invalid, stale, unsupported or non-releasable evidence; never recover by guessing."""


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_pairs,
                          parse_constant=lambda s: (_ for _ in ()).throw(EvidenceError(f'Invalid JSON constant: {s}')))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f'Cannot read valid JSON from {path}: {exc}') from exc


def schema_bundle():
    return {p.name: load_json(p) for p in sorted(SCHEMA_DIR.glob('*.schema.json'))}


def validate_schema(value, name):
    bundle = schema_bundle()
    registry = Registry().with_resources(
        (schema['$id'], Resource.from_contents(schema)) for schema in bundle.values())
    schema = bundle[name + '.schema.json']
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        first = errors[0]
        raise EvidenceError(f'Schema {name} at {list(first.path)}: {first.message}')


def record_digest(record):
    # Review binds source identity, field locators and values, not publication permission.
    return digest({key: record[key] for key in ('id', 'source_id', 'document_sha256', 'locator', 'observations')})


def source_digest(source):
    return digest({key: value for key, value in source.items() if key not in ('review', 'publication')})


def _require(condition, message):
    if not condition:
        raise EvidenceError(message)


def safe_url(value):
    parsed = urlsplit(value)
    _require(parsed.scheme in ('https', 'http') and bool(parsed.hostname)
             and parsed.username is None and parsed.password is None
             and not any(ord(c) < 33 for c in value), 'Unsafe source URL')


def _index(items, label):
    result = {item['id']: item for item in items}
    _require(len(result) == len(items), f'Duplicate {label} identifier')
    return result


def _validate_observation(obs, source):
    expected = FIELD_BINDINGS[source['source_class']].get(obs['source_field'])
    _require(expected == obs['kind'], 'Source field/kind mismatch or unsupported field')
    kind, raw, value = obs['kind'], obs['raw_value'], obs['value']
    _require(obs['observation_date'] is None and bool(obs['missing_date_reason']),
             'This historical input class requires unknown observation date and its reason')
    if kind in MONEY or kind == 'reported_percent_complete':
        _require(bool(re.fullmatch(r'(0|[1-9][0-9]*)(\.[0-9]{1,2})?', value)), 'Invalid decimal string')
        try:
            amount = Decimal(value)
        except InvalidOperation as exc:
            raise EvidenceError('Invalid decimal') from exc
        raw_pattern = r'(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?'
        numeric_raw = raw.removesuffix('%') if kind == 'reported_percent_complete' else raw
        _require(bool(re.fullmatch(raw_pattern, numeric_raw)), 'Malformed source numeric text')
        _require(Decimal(numeric_raw.replace(',', '')) == amount, 'Raw/normalized amount mismatch')
        _require(obs['normalization'] == ('percent' if kind == 'reported_percent_complete' else 'grouped_decimal'),
                 'Invalid numeric normalization method')
        if kind == 'reported_percent_complete':
            _require(amount <= 100 and obs['currency'] is None, 'Invalid reported percentage')
        else:
            _require(obs['currency'] == 'NGN', 'Currency missing or incorrect')
    else:
        _require(obs['currency'] is None, 'Non-money observation has currency')
        if kind == 'award_date':
            try:
                if source['source_class'] == 'open_contracting':
                    normalized = datetime.fromisoformat(raw.replace('Z', '+00:00')).date().isoformat()
                    method = 'iso_datetime_date'
                else:
                    normalized = (datetime.strptime(raw, '%B %d, %Y') if raw != '14th Nov., 2013'
                                  else datetime.strptime(raw, '%dth %b., %Y')).date().isoformat()
                    method = 'english_date'
            except ValueError as exc:
                raise EvidenceError('Unrecognized explicit award date') from exc
            _require(obs['normalization'] == method and normalized == value, 'Award date mismatch')
        else:
            _require(obs['normalization'] == 'identity' and raw == value, 'Unreviewed text normalization')
    if kind == 'annual_appropriation':
        _require(isinstance(obs['fiscal_year'], int), 'Annual appropriation lacks fiscal year')
    else:
        _require(obs['fiscal_year'] is None, 'Fiscal year must not be inferred for another field')


def validate_input(data, release=False):
    validate_schema(data, 'reviewed-input')
    sources = _index(data['sources'], 'source')
    records = _index(data['records'], 'record')
    decisions = _index(data['identity_decisions'], 'decision')
    anchor = data['project']['anchor_record_id']
    _require(anchor in records, 'Missing anchor record')
    _require(sources.get(records[anchor]['source_id'], {}).get('source_class') == 'appropriation',
             'Dossier anchor must be an appropriation record')
    all_obs, owner = {}, {}
    record_locations = set()
    for source in sources.values():
        safe_url(source['url'])
        _require(source_digest(source) == source['review']['content_sha256'], 'Reviewed source metadata digest mismatch')
    for record in records.values():
        _require(record['source_id'] in sources, 'Missing source provenance')
        stable_location = (record['source_id'], canonical(record['locator']))
        _require(stable_location not in record_locations, 'Duplicate source record locator')
        record_locations.add(stable_location)
        source = sources[record['source_id']]
        _require(('line' in record['locator']) == (source['format'] == 'JSONL_GZIP'), 'Locator/source format mismatch')
        _require((source['source_class'] == 'open_contracting') == (source['format'] == 'JSONL_GZIP'), 'Source class/format mismatch')
        _require(record['document_sha256'] == sources[record['source_id']]['sha256'], 'Record/document hash mismatch')
        _require(record_digest(record) == record['review']['content_sha256'], 'Reviewed record digest mismatch')
        fields = set()
        for obs in record['observations']:
            _require(obs['id'] not in all_obs, 'Duplicate observation identifier')
            _require(obs['source_field'] not in fields, 'Duplicate source field in a record')
            fields.add(obs['source_field'])
            _validate_observation(obs, sources[record['source_id']])
            all_obs[obs['id']], owner[obs['id']] = obs, record['id']
    by_record = {}
    for decision in decisions.values():
        rid = decision['record_id']
        _require(rid in records and rid not in by_record, 'Missing or duplicate record decision')
        _require(decision['project_id'] == data['project']['id'] and decision['anchor_record_id'] == anchor,
                 'Decision points to wrong project/anchor')
        _require(decision['record_sha256'] == record_digest(records[rid]) and
                 decision['anchor_sha256'] == record_digest(records[anchor]), 'Stale resolution decision')
        for basis in decision['basis']:
            _require(all(oid in all_obs and owner[oid] in (rid, anchor) for oid in basis['observation_ids']),
                     'Resolution basis has missing or unrelated observation provenance')
        if decision['state'] == 'RESOLVED_MATCH' and rid != anchor:
            # Explicit human-reviewed route/scope remains necessary; this is a guard,
            # never an automatic identity resolver based on an equal number.
            a = [o['value'] for o in records[anchor]['observations'] if o['kind'] == 'contract_number']
            b = [o['value'] for o in records[rid]['observations'] if o['kind'] == 'contract_number']
            _require(len(a) == len(b) == 1 and a == b, 'Resolved cross-record contract identifiers differ')
            used = {oid for item in decision['basis'] for oid in item['observation_ids']}
            _require(all(any(owner[oid] == record_id and all_obs[oid]['kind'] == 'route' for oid in used)
                         for record_id in (anchor, rid)), 'Missing explicit route comparison basis')
            _require(not decision['counterevidence'], 'Unresolved counterevidence cannot enter an accepted link')
        by_record[rid] = decision
    _require(set(by_record) == set(records), 'Every record needs exactly one identity decision')
    _require(by_record[anchor]['state'] == 'RESOLVED_MATCH', 'Anchor not accepted')
    excluded = {}
    for item in data['exclusions']:
        oid = item['observation_id']
        _require(oid in all_obs and oid not in excluded, 'Missing or duplicate excluded observation')
        excluded[oid] = item
    coverage = data['coverage']
    _require(set(coverage['reviewed_source_ids']) == set(sources), 'Incomplete source coverage provenance')
    _require(set(coverage['reviewed_record_ids']) == set(records), 'Incomplete record coverage provenance')
    for attempt in coverage['attempts']:
        safe_url(attempt['source_url'])
    if release:
        dispositions = [data['publication'], coverage['publication']]
        dispositions += [s['publication'] for s in sources.values()]
        dispositions += [r['publication'] for r in records.values()]
        for disposition in dispositions:
            _require(disposition['disposition'] in APPROVED_REUSE and
                     bool(disposition['authority']) and bool(disposition['reference']),
                     'Publication blocked: unapproved content or missing rights authority')
    return sources, records, by_record, excluded


def compile_evidence(data, *, release=False):
    sources, records, decisions, exclusions = validate_input(data, release)
    rules = load_json(RULES_PATH)
    _require(tuple(rules['dimensions']) == DIMENSIONS, 'Rule dimension ordering invalid')
    partitions = {'accepted': [], 'candidates': [], 'excluded': []}
    for rid, record in sorted(records.items()):
        decision = decisions[rid]
        base = {'record_id': rid, 'source_id': record['source_id'], 'locator': record['locator'],
                'identity_decision_id': decision['id'], 'identity_state': decision['state'],
                'review': record['review'], 'publication': record['publication'],
                'document_sha256': record['document_sha256']}
        admitted = []
        for obs in sorted(record['observations'], key=lambda o: o['id']):
            if obs['id'] in exclusions:
                partitions['excluded'].append(dict(base, observation=obs, exclusion=exclusions[obs['id']]))
            else:
                admitted.append(obs)
        if admitted:
            bucket = 'accepted' if decision['state'] == 'RESOLVED_MATCH' else 'candidates'
            partitions[bucket].append(dict(base, observations=admitted))
    accepted = [(r, obs) for r in partitions['accepted'] for obs in r['observations']]
    findings = []
    common = 'Historical source statement; observation date unknown. This does not establish present-day condition.'
    for record, obs in accepted:
        source = sources[record['source_id']]
        kind, value = obs['kind'], obs['value']
        label = rules['financial_labels'].get(kind, kind.replace('_', ' '))
        display = f"NGN {Decimal(value):,}" if kind in MONEY else value
        if kind == 'annual_appropriation':
            display += f" (fiscal year {obs['fiscal_year']})"
        if kind == 'reported_percent_complete':
            display += '%'
        text = f"{source['title']} records {label}: {display}."
        qualification = common if source['source_class'] == 'official_implementation' else source['limitations'][0]
        if kind == 'amount_certified':
            qualification += ' Amount certified is not independently verified treasury payment.'
        findings.append({'id': 'observation:' + obs['id'], 'subject': record['record_id'],
                         'proposition': text, 'evidence_state': 'SUPPORTED', 'rule_id': 'R01/R03/R04',
                         'observation_refs': [obs['id']], 'coverage_refs': [], 'qualification': qualification})
    # Only annual provisions for the identical code, fiscal year and currency
    # are comparable in this corpus. Unknown-date Works values are not compared.
    annual_groups = {}
    for record in partitions['accepted']:
        codes = [o['value'] for o in record['observations'] if o['kind'] == 'project_code']
        if len(codes) == 1:
            for obs in record['observations']:
                if obs['kind'] == 'annual_appropriation':
                    annual_groups.setdefault((codes[0], obs['fiscal_year'], obs['currency']), []).append(obs)
    conflicts = [group for group in annual_groups.values() if len({Decimal(o['value']) for o in group}) > 1]
    for i, group in enumerate(conflicts):
        findings.append({'id': f'comparison:{i}', 'subject': data['project']['id'],
                         'proposition': 'A single annual provision is established for this project code and fiscal year.',
                         'evidence_state': 'CONFLICTING', 'rule_id': 'R08:comparable-annual-provision',
                         'observation_refs': [o['id'] for o in group], 'coverage_refs': [data['coverage']['id']],
                         'qualification': 'Admitted records for the same project code, fiscal year and currency disagree. Neither value is selected or summed; this is not an allegation.'})
    for decision in decisions.values():
        if decision['state'] != 'RESOLVED_MATCH':
            findings.append({'id': 'identity:' + decision['id'], 'subject': decision['record_id'],
                             'proposition': 'This candidate record refers to the dossier project scope.',
                             'evidence_state': 'UNVERIFIABLE', 'rule_id': 'R02:unresolved-identity',
                             'observation_refs': [],
                             'coverage_refs': [data['coverage']['id']],
                             'qualification': 'Candidate evidence is not admitted to project findings. ' + ' '.join(decision['counterevidence']) + ' ' + decision['scope']})
    stages = []
    for dimension, rule in rules['dimensions'].items():
        relevant, sufficient = [], False
        for record in partitions['accepted']:
            if sources[record['source_id']]['source_class'] != rule['source_class']:
                continue
            kinds = {obs['kind'] for obs in record['observations']}
            sufficient |= set(rule['required_kinds']).issubset(kinds)
            relevant += [obs['id'] for obs in record['observations'] if obs['kind'] in rule['partial_kinds']]
        state = 'SUPPORTED' if sufficient else 'INCOMPLETE' if relevant else 'UNVERIFIABLE'
        if dimension == 'appropriation' and conflicts:
            state = 'CONFLICTING'
        fid = 'stage:' + dimension
        if state == 'UNVERIFIABLE':
            qualification = 'No qualifying admitted evidence is included in the reviewed corpus; this does not establish nonexistence.'
        elif dimension == 'appropriation':
            qualification = 'The schedule is not independently authenticated as the final signed legal instrument.'
        else:
            qualification = common + ' Required primary or independent evidence for the stronger proposition is not included.'
        findings.append({'id': fid, 'subject': data['project']['id'], 'proposition': rule['proposition'],
                         'evidence_state': state, 'rule_id': 'R07:' + dimension,
                         'observation_refs': sorted(relevant), 'coverage_refs': [data['coverage']['id']],
                         'qualification': 'This state applies only to the reviewed corpus and stated proposition. ' + qualification})
        stages.append({'dimension': dimension, 'proposition': rule['proposition'],
                       'evidence_state': state, 'finding_id': fid})
    progress = [obs['id'] for _, obs in accepted if obs['kind'] == 'reported_percent_complete']
    completion_context = (
        'Historical reported progress does not establish '
        'present-day condition; its observation date remains unknown.'
        if progress else
        'No qualifying admitted completion evidence is included in the reviewed corpus, '
        'and present-day condition is not established.'
    )
    findings.append({'id': 'completion', 'subject': data['project']['id'],
                     'proposition': 'The project was completed.',
                     'evidence_state': 'UNVERIFIABLE', 'rule_id': 'R07:completion-historical-only',
                     'observation_refs': progress, 'coverage_refs': [data['coverage']['id']],
                     'qualification': 'Only historical documentary reporting is admitted by this corpus; '
                     'even a reported 100% would not independently establish current physical condition.'})
    known = []
    for record, obs in accepted:
        if obs['kind'] in {'annual_appropriation', 'contract_sum', 'amount_certified', 'reported_percent_complete'}:
            finding = next(f for f in findings if f['id'] == 'observation:' + obs['id'])
            known.append({'text': finding['proposition'] + ' ' + finding['qualification'],
                          'finding_refs': [finding['id']]})
    if not known:
        known.append({'text': 'No accepted financial or implementation observations are established in this reviewed corpus.',
                      'finding_refs': ['stage:appropriation', 'stage:implementation']})
    answers = [
        {'question_id': 'known', 'question': 'What do we actually know about this project?', 'clauses': known},
        {'question_id': 'payment', 'question': 'What payment evidence is available?', 'clauses': [
            {'text': 'The available evidence does not establish an independently verified treasury payment '
                     'for this project. An amount certified is not verified payment.', 'finding_refs': ['stage:payment']}]},
        {'question_id': 'completed', 'question': 'Was this project completed?', 'clauses': [
            {'text': 'The available evidence does not establish that this project was completed. '
                     + completion_context, 'finding_refs': ['completion']}]},
    ]
    for record in partitions['candidates']:
        if any(o['kind'] == 'transaction_value' for o in record['observations']):
            answers[1]['clauses'].append({
                'text': 'A candidate procurement record contains a transaction value, but its project identity is unresolved. '
                        'The reviewed record lacks a payment date and named payee; no independent treasury corroboration is included.',
                'finding_refs': ['stage:payment', 'identity:' + record['identity_decision_id']]})
    semantic = {'schema_version': data['schema_version'], 'corpus_version': data['corpus_version'],
                'rules_version': rules['rules_version'], 'publication_mode': 'RELEASABLE' if release else 'LOCAL_REVIEW',
                'publication': data['publication'], 'hashes': {
                    'input_sha256': digest(data), 'rules_sha256': digest(rules),
                    'schemas_sha256': digest(schema_bundle()),
                    'compiler_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                'project': data['project'], 'sources': [sources[k] for k in sorted(sources)],
                'coverage': data['coverage'], 'identity_decisions': sorted(data['identity_decisions'], key=lambda d: d['id']),
                'evidence': partitions, 'findings': findings, 'stages': stages, 'answers': answers,
                'limitations': rules['limitations']}
    artifact = copy.deepcopy({'semantic': semantic, 'semantic_sha256': digest(semantic)})
    validate_schema(artifact, 'artifact')
    return artifact


def verify_artifact(artifact, reviewed_input, *, release=False):
    validate_schema(artifact, 'artifact')
    _require(digest(artifact['semantic']) == artifact['semantic_sha256'], 'Artifact semantic hash mismatch')
    expected = compile_evidence(reviewed_input, release=release)
    _require(artifact == expected, 'Artifact is stale, tampered, wrong-mode, or built with different inputs/rules/schemas/compiler')


def write_artifact(path, artifact):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    try:
        temporary.write_bytes(canonical(artifact) + b'\n')
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['compile', 'verify'])
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--release', action='store_true', help='Enforce publication dispositions; does not authorize publication')
    args = parser.parse_args(argv)
    try:
        _require(args.input.resolve() != args.output.resolve(), 'Input and output paths must differ')
        data = load_json(args.input)
        if args.command == 'compile':
            # All checks finish before touching output. A pre-existing file is not
            # a successful result after this process fails; consumers must verify it.
            artifact = compile_evidence(data, release=args.release)
            write_artifact(args.output, artifact)
        else:
            artifact = load_json(args.output)
            verify_artifact(artifact, data, release=args.release)
        print(json.dumps({'result': 'PASS', 'command': args.command,
                          'mode': artifact['semantic']['publication_mode'],
                          'semantic_sha256': artifact['semantic_sha256']}))
        return 0
    except (EvidenceError, OSError) as exc:
        print(json.dumps({'result': 'FAIL', 'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
