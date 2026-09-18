# Gate 7 publication register

Review date: 18 September 2026. Reviewer: CivicProof Controller acting within the Operator's Gate 7 source/content review authorization. `APPROVED_FOR_RELEASE` below is an exact-content eligibility disposition for the local release candidate, not permission to publish and not legal certification. Gate 7 approval remains with the Operator.

## Basis and limits

The Nigerian Copyright Commission's [Copyright Act, 2022, sections 2(5), 3(a) and 3(b)](https://www.copyright.gov.ng/CopyrightAct/CopyrightAct2023FinalPublication1.pdf) distinguishes underlying data from copyright in compilations and excludes mere data and specified official texts from eligibility. This review applies that distinction narrowly to selected factual fields, identifiers and individual administrative record entries. It does not assert a blanket government-work exemption, an upstream open license, or unrestricted rights in a whole report, database, compilation, layout or image.

The [OCP registry's Nigeria entry](https://data.open-contracting.org/en/publication/64) identifies BPP/NOCOPO as the origin and links a NOCOPO license page. Both HTTP and HTTPS license fetches returned a gateway failure during this review; the actual license terms remain unestablished. OCP's own website-content license is not treated as a license for the third-party dataset. Only the selected factual fields from two records are eligible below. The broad snapshot, its arrangement, all other records and substantial narrative excerpts are excluded.

No express redistribution license was established for the appropriation or Works PDFs. Eligibility below rests on the narrow factual/administrative character of the specific selected fields, not their mere online availability. The source documents and their reproductions remain excluded. This is a reasoned publication review with residual jurisdictional/legal uncertainty, not a warranty of rights.

## Source-by-content dispositions

| Content/category | Source | Exact proposed representation | Disposition | Basis / restrictions | Attribution |
|---|---|---|---|---|---|
| Normalized financial values, currency, percentages and dates | Appropriation schedule, historical Works, two NOCOPO/OCP records | Selected scalar fields for the five dossiers; no aggregation | APPROVED_FOR_RELEASE | Underlying data; preserve type, unknown dates, candidates/exclusions; no database export | Institution, document title, URL, field and locator |
| Route/project titles, agency/contractor names, contract/project identifiers | Same sources | Minimal identifying factual names and route/scope strings already in approved inputs | APPROVED_FOR_RELEASE | Identifying data/individual administrative entries, not source compilation or layout; no current-status inference | Same |
| Raw source-field numeric/date text and short labels | Same sources | Exact selected scalar spelling alongside normalized value | APPROVED_FOR_RELEASE | Needed to show faithful transcription; not whole rows/tables/pages; preserve commas, percent sign, field names | Same |
| Short Works remarks | Historical Works | `Work in progress`, `Slow work progress`, and the single C06 factual administrative remark about absence since September 2016 and unsuccessful return efforts | APPROVED_FOR_RELEASE | Individually reviewed factual administrative statements, not a substantial excerpt; C06 remains historical, date of observation unknown; do not infer current abandonment | Works title/institution/URL/page/row |
| Planning/milestone descriptions and statuses | Two NOCOPO/OCP records | Only selected route/contract-reference/assessment/approval wording required to explain competing identity and wrong-road exclusion | APPROVED_FOR_RELEASE | Individual administrative facts; preserve candidate/excluded status; `met` is not physical completion | BPP/NOCOPO origin, OCP mirror, snapshot line/OCID/JSON Pointer |
| Source URLs, page/row/line/field locators, hashes, retrieval metadata | CivicProof provenance of all three sources | Links and integrity metadata | APPROVED_FOR_RELEASE | Metadata, not source bytes; hashes do not establish truth | Preserve publisher and mirror distinction |
| Derived findings, qualifications, identity decisions and coverage summaries | CivicProof, Operator-reviewed | Existing bounded statements unchanged; publication metadata overlaid separately | APPROVED_FOR_RELEASE | CivicProof-authored interpretation, never a new upstream fact; preserve human gate/identity authority | CivicProof; source refs retained |
| Verification JSON and search index | CivicProof compilation of approved units | Deterministically compiled exact selected units and own findings | APPROVED_FOR_RELEASE | Eligible only if every input leaf is approved and semantic baseline matches; no independent data license inferred | Embedded sources plus DATA_NOTICE.md |
| CivicProof-owned application/pipeline/tests/docs | CivicProof | Allowlisted code and release-specific documentation | APPROVED_FOR_RELEASE | Operator selected MIT for owned code; third-party code retains its licenses; no blanket MIT on data | LICENSE, dependency license notices |
| CivicProof application screenshots | CivicProof UI with eligible data | Only screenshots captured from this release candidate | APPROVED_FOR_RELEASE | Inherits unit approvals of the displayed data; never source-page renders | CivicProof and linked data notice |
| Longer source excerpts, full tables, source PDF documents | All sources | None | EXCLUDED_FROM_RELEASE | No need for product; document/compilation rights not established | Original links only |
| PDF page renders, extracted full text and page-render archives | Appropriation / Works | None | EXCLUDED_FROM_RELEASE | Derived full-source reproductions not needed | Original locators only |
| Broad OCP snapshot / national compilation / unused records | BPP/NOCOPO via OCP | None | EXCLUDED_FROM_RELEASE | No express dataset license established; no necessity to reproduce whole collection | Mirror URL and hash metadata only |
| Private research docs, review ZIPs, agent transcripts, scratch/cache material, private email | Private workspace | None | EXCLUDED_FROM_RELEASE | Not product data; unrelated or private content | Public release documentation substitutes only owned explanations |
| Unreviewed new fields/excerpts/sources | Any | None | PENDING | Fail closed; no authorization to expand corpus | Requires a new exact-content review |

Approving reviewer/date for every approved row: Controller content review, 18 September 2026, under `08_OPERATOR_GATES_5_6_APPROVAL_GATE_7_AUTHORIZATION.md`; MIT choice separately supplied by the Operator. No claimed signature, institutional permission or upstream rights grant is invented.

## Machine binding

The candidate's `publication/register.json` binds every scalar leaf of every released input to its content category, originating source where applicable, SHA-256 of the exact value, attribution requirement, disposition, basis, reviewer and date. `pipeline.build_local.validate_publication` rejects missing/extra units, stale values and PENDING/EXCLUDED categories. Public artifacts must also match frozen protected semantic digests. Publicity metadata is overlaid on copies; the private records remain byte-unchanged.

The exact file allowlist separately approves source code, metadata and documents by file hash. Derived artifacts/index are checked by recompilation from the registered input units. Screenshot approvals reference their release-build capture; old local-review screenshots are not copied. These are auditable technical controls, not legal certification.
