# CivicProof

**What can public records actually establish about this project?**

CivicProof helps an ordinary citizen inspect public-project evidence without having to assemble a case from scattered records. It is a Transparency & Accountability proof of concept for the OSF × Andela hackathon, built from a human-originated thesis and a bounded five-dossier historical Nigerian roads corpus.

This is the approved public CivicProof hackathon proof of concept. [Live demo](https://civicproof.pages.dev) · [Public repository](https://github.com/Kaycee-dev/CivicProof). Operator Gate 7 release approval, public repository verification and live smoke tests are complete. Hackathon submission is not yet authorized.

## What you can do

1. Search locally by project/route, agency, location, reference or keyword.
2. Read an evidence dossier.
3. Inspect five evidence dimensions: appropriation, procurement, award, payment and implementation.
4. Open a provenance drawer showing raw selected scalar values, normalized values, source fields/locators and attribution.
5. See why records were admitted, left as candidates or excluded.
6. Ask exactly three fixed evidence questions: what is known, payment evidence, and completion.
7. Download the exact verification JSON behind the screen.

The corpus is C01, C02, C06, C09 and C12. C01/C02 concern different sections of the Enugu–Port Harcourt corridor (6208 versus 6209). C09 has an unresolved Works candidate despite a shared contract number. C12 retains two competing procurement candidates and excludes a milestone referring to a different road. No candidate value is silently promoted.

## What the states mean

SUPPORTED means admitted reviewed records support the stated proposition, not that a government claim is independently proved true in the real world. INCOMPLETE means relevant admitted evidence exists but is insufficient. UNVERIFIABLE means the reviewed corpus does not establish the proposition. CONFLICTING is reserved for comparable admitted evidence that disagrees. Missing or unresolved dimensions are meaningful results, not proof of nonexistence.

RESOLVED_MATCH, POSSIBLE_MATCH and explicit exclusions describe admission separately from evidence state. Historical progress is not current condition; certified amount is not independently verified treasury payment. None of the five dossiers establishes treasury payment or project completion.

## Trust architecture

Registered public factual inputs → explicit reviewed identity/exclusion decisions → strict Python validation → deterministic evidence rules → versioned artifacts → hash-pinned static Next.js presentation → download of the same bytes.

There is no runtime LLM, API key, backend application, database or required source fetch. The browser does not create conclusions. Missing, corrupt, wrong-project or stale artifacts fail closed. The local/static host serves files only. Optional source links can fail without removing local evidence. A fully old application bundle cannot discover a newer edition without an external version authority.

Every released input leaf maps to `publication/register.json`; missing, altered or PENDING material stops compilation. Frozen product digests constrain the public transformation. See [data notice](DATA_NOTICE.md), [publication register](docs/PUBLICATION_REGISTER.md) and [verified claims](docs/VERIFIED_RELEASE_CLAIMS.md).

## Install, build, test and run

Use Python 3.11 or newer and Node 22 with npm. Initial dependency installation requires network access. From this candidate root:

```sh
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell alternative: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pipeline.build_local
python -m unittest discover -s tests -p 'test_public.py' -v
cd apps/web
npm ci
npm run build
cd ../..
python -m http.server 3000 --bind 127.0.0.1 --directory apps/web/out
```

Open http://127.0.0.1:3000. `npm run build` regenerates and validates the public artifacts first. No private inputs, research originals or previous build output are needed. The release includes five approved factual input copies under `data/public_inputs/`; the private reviewed records are not modified.

For browser tests, install a browser once, then keep the static server running in another terminal:

```sh
cd apps/web
npx playwright install chromium
npm test
node scripts/demo.mjs
```

An existing Chromium executable may be selected with `BROWSER_EXECUTABLE`. Linux containers may use `/usr/bin/chromium`; installation may require browser OS dependencies. `PLAYWRIGHT_BASE_URL` defaults to http://127.0.0.1:3000. Browser tests block external requests.

Public tests cover frozen semantics, candidates/exclusions, answer grounding, financial types, provenance, safe URLs, publication rejection, stale artifacts, references, search, deterministic regeneration and UI/export parity. The private source-transcription/hash tests require excluded originals; they are a different test layer and are not silently skipped or presented as public reproduction passes.

## Golden demo

Search Umuahia → C01 → five dimensions → provenance → distinguish appropriation, contract sum and certification → payment/completion questions → unresolved C09/C12 → exact verification export. The approved local implementation has completed this paced 2–4 minute flow. The release reproduction record independently records the actual candidate run; the automated pacing includes narration dwell time and is not a human usability trial.

Screenshots generated from this candidate: [search](docs/screenshots/search.png), [strong dossier](docs/screenshots/C01-dossier.png), [provenance](docs/screenshots/provenance.png), [unresolved C12](docs/screenshots/C12-dossier.png). These locally captured screens use the same artifacts as the verified public demo.

## AI-use disclosure

The founding civic problem, motivation and governing thesis originated with the human Operator. AI agents assisted substantially with public-record research, extraction/transcription, source comparison, product/architecture proposals, code, adversarial tests, evaluation and documentation. This includes autonomous tool use and separately tasked AI reviewers; it is not merely autocomplete. The Operator approved identity boundaries and gates. Deterministic software—not a runtime model—assigns evidence states and fixed answers. AI evaluation does not certify government truth, current physical condition or legal compliance.

## Sources, limitations and non-claims

See [DATA_NOTICE.md](DATA_NOTICE.md) for institutions, URLs, exact publication treatment and limitations. Source documents, page images, national snapshots and broad research extracts are not redistributed. Rights review covers only the selected factual/administrative fields; it does not grant an upstream license.

CivicProof does not detect corruption, prove theft, trace every naira, verify current completion, independently verify treasury payments or cover Nigerian spending nationally. Hashes identify bytes, not truth. The appropriation schedule is not independently authenticated as the final signed instrument. Effective Works observation dates remain unknown. C09/C12 remain unresolved. Keyboard/narrow-screen testing is not a comprehensive accessibility audit or citizen usability study.

**License:** CivicProof-owned source code is released under the MIT License. Third-party source data and factual extracts are subject to their respective source terms and this repository's `DATA_NOTICE.md`; the MIT License does not grant rights over those materials. Dependencies retain their own licenses.
