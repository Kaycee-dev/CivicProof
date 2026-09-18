import manifest from './build-manifest.json';
export type Observation = { id: string; kind: string; source_field: string; raw_value: string; value: string; currency: string | null; fiscal_year: number | null; observation_date: string | null; missing_date_reason: string | null };
export type RecordEvidence = { record_id: string; source_id: string; document_sha256: string; locator: { page?: number; line?: number; row: string }; identity_state: string; identity_decision_id: string; observations: Observation[] };
export type Finding = { id: string; proposition: string; evidence_state: string; qualification: string; observation_refs: string[]; coverage_refs: string[] };
export type Artifact = { semantic_sha256: string; semantic: {
 project: { id: string; title: string }; publication_mode: string; sources: { id: string; institution: string; title: string; url: string; sha256: string; retrieved_at: string; limitations: string[] }[];
 evidence: { accepted: RecordEvidence[]; candidates: RecordEvidence[]; excluded: (Omit<RecordEvidence, 'observations'> & { observation: Observation; exclusion: { reason: string; propositions: string[] } })[] };
 findings: Finding[]; stages: { dimension: string; proposition: string; evidence_state: string; finding_id: string }[];
 answers: { question_id: string; question: string; clauses: { text: string; finding_refs: string[] }[] }[];
 identity_decisions: { id: string; state: string; scope: string; basis: { statement: string; observation_ids: string[] }[]; counterevidence: string[] }[];
 limitations: string[]; coverage: { limitations?: string[] }; hashes: Record<string, string>;
}};
export type SearchIndex = { scope: string; projects: { id: string; title: string; terms: string[] }[] };
async function checked(path: string, expected: string) {
 const response = await fetch(path, { cache: 'no-store' });
 if (!response.ok) throw new Error('Evidence unavailable');
 const raw = await response.arrayBuffer();
 const actual = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)), b => b.toString(16).padStart(2, '0')).join('');
 if (actual !== expected) throw new Error('Evidence unavailable');
 return { raw, data: JSON.parse(new TextDecoder().decode(raw)) };
}
export async function loadIndex(): Promise<SearchIndex> { return (await checked('/data/index.json', manifest.index)).data; }
export async function loadArtifact(id: string): Promise<{raw: ArrayBuffer; data: Artifact}> {
 const hash = manifest.artifacts[id as keyof typeof manifest.artifacts];
 if (!hash) throw new Error('Evidence unavailable');
 return checked(`/data/${id}.json`, hash);
}
export function label(kind: string) { return ({annual_appropriation: 'Annual appropriation · schedule amount', planning_amount: 'Planning amount', tender_value: 'Tender value', award_value: 'Award value', contract_sum: 'Reported contract sum', amount_certified: 'Amount certified · not verified payment', transaction_value: 'Transaction value · not verified payment', reported_percent_complete: 'Historical reported progress'} as Record<string,string>)[kind] || kind.replaceAll('_', ' '); }
export function value(o: Observation) { const parts = o.value.split('.'); return o.currency ? `${o.currency} ${parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')}${parts[1] ? '.' + parts[1] : ''}` : o.kind === 'reported_percent_complete' ? `${o.value}%` : o.value; }
export function locator(r: RecordEvidence) { return `${r.locator.page ? 'Page '+r.locator.page : 'Snapshot line '+r.locator.line} · ${r.locator.row}`; }
