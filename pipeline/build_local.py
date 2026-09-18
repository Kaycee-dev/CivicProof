"""Public-only reproducible compilation. No private research paths or network."""
import copy
import hashlib
from pathlib import Path
from pipeline import compiler as c

IDS = ('C01', 'C02', 'C06', 'C09', 'C12')

def leaves(value, prefix=''):
    if isinstance(value, dict):
        for key in sorted(value):
            yield from leaves(value[key], prefix + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from leaves(item, prefix + '/' + str(i))
    else:
        yield prefix, value

def protected_semantics(artifact):
    """Only publication bookkeeping is excluded from the frozen product digest."""
    s = copy.deepcopy(artifact['semantic'])
    s.pop('hashes')
    s.pop('publication_mode')
    def strip(value):
        if isinstance(value, dict):
            value.pop('publication', None)
            for v in value.values(): strip(v)
        elif isinstance(value, list):
            for v in value: strip(v)
    strip(s)
    # This single final limitation describes publication authority, not evidence.
    s['limitations'] = s['limitations'][:-1]
    return c.digest(s)

def validate_publication(pid, data, register):
    units = register['units'][pid]
    actual = dict(leaves(data))
    c._require(set(actual) == set(units), 'Publication unit set differs: absent or unexpected content')
    for pointer, value in actual.items():
        unit = units[pointer]
        c._require(unit['disposition'] == 'APPROVED_FOR_RELEASE' and
                   unit['value_sha256'] == c.digest(value) and
                   unit['category'] in register['categories'] and
                   register['categories'][unit['category']]['disposition'] == 'APPROVED_FOR_RELEASE' and
                   bool(unit['reviewer']) and bool(unit['basis']) and bool(unit['review_date']),
                   'Publication missing, pending, excluded or stale at ' + pointer)

def compile_public(pid, data=None, register=None):
    register = register or c.load_json(c.ROOT / 'publication/register.json')
    data = data or c.load_json(c.ROOT / f'data/public_inputs/{pid}.json')
    validate_publication(pid, data, register)
    artifact = c.compile_evidence(data, release=True)
    frozen = c.load_json(c.ROOT / 'publication/semantic-baseline.json')
    c._require(protected_semantics(artifact) == frozen[pid], 'Frozen product semantics changed')
    return artifact

def build():
    artifacts = {pid: compile_public(pid) for pid in IDS}
    index = []
    for pid, artifact in artifacts.items():
        s = artifact['semantic']
        obs = [o for r in s['evidence']['accepted'] for o in r['observations']]
        terms = sorted({o['value'] for o in obs if o['kind'] in
                        ('route', 'agency', 'location', 'contract_number', 'project_code')})
        index.append({'id': pid, 'title': s['project']['title'], 'terms': terms})
    raw_index = c.canonical({'scope': 'Five historical road dossiers; not a national project register.', 'projects': index}) + b'\n'
    assets = c.ROOT / 'apps/web/public/data'; assets.mkdir(parents=True, exist_ok=True)
    out = c.ROOT / 'data/artifacts'; out.mkdir(parents=True, exist_ok=True)
    manifest = {'artifacts': {}, 'index': hashlib.sha256(raw_index).hexdigest()}
    for pid, artifact in artifacts.items():
        raw = c.canonical(artifact) + b'\n'
        (out / f'{pid}.json').write_bytes(raw)
        (assets / f'{pid}.json').write_bytes(raw)
        manifest['artifacts'][pid] = hashlib.sha256(raw).hexdigest()
    (out / 'index.json').write_bytes(raw_index)
    (assets / 'index.json').write_bytes(raw_index)
    (c.ROOT / 'apps/web/lib/build-manifest.json').write_bytes(c.canonical(manifest) + b'\n')
    print(c.canonical(manifest).decode())
    return manifest

if __name__ == '__main__': build()
