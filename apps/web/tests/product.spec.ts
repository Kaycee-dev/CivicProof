import {createHash} from 'node:crypto';
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve('../..');
const evidence=path.join(root,'verification/product');
fs.mkdirSync(evidence,{recursive:true});
const ids=['C01','C02','C06','C09','C12'];
test.beforeEach(async({context})=>{
 await context.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort('internetdisconnected'));
});
test('U01 local bounded search',async({page})=>{
 await page.goto('/');await expect(page.locator('.result')).toHaveCount(5);
 for(const query of ['Umuahia','6208','Anambra','Works','ERGP12130209','Isseke']){await page.getByLabel('Project, route, agency, location or reference').fill(query);await expect(page.locator('.result').first()).toBeVisible();}
 await page.locator('#search').fill('6208');await expect(page.locator('.result')).toHaveCount(1);await expect(page.locator('.result')).toContainText('C01');
 await page.locator('#search').fill('6209');await expect(page.locator('.result')).toHaveCount(1);await expect(page.locator('.result')).toContainText('C02');
 await page.locator('#search').fill('unrelated submarine');await expect(page.getByText('No match in this demonstration corpus')).toBeVisible();await expect(page.getByText(/does not mean that no such government project exists/)).toBeVisible();
 await page.locator('#search').fill('');await page.screenshot({path:path.join(evidence,'search.png'),fullPage:true});
});
for(const id of ids)test(`E18 U04 ${id} display/export parity with external network blocked`,async({page,context})=>{
 const original=fs.readFileSync(path.join(root,`data/artifacts/${id}.json`));const artifact=JSON.parse(original.toString());const s=artifact.semantic;
 await page.goto(`/projects/${id}/`);await expect(page.getByRole('heading',{level:1})).toHaveText(s.project.title);
 await expect(page.locator('.dimension')).toHaveCount(5);
 for(const stage of s.stages){const card=page.locator('.dimension').filter({has:page.getByRole('heading',{name:stage.dimension,exact:true})});await expect(card).toContainText(stage.proposition);await expect(card).toContainText(stage.evidence_state);}
 for(const f of s.findings.filter((f:any)=>f.id.startsWith('observation:'))){const financial=s.evidence.accepted.flatMap((r:any)=>r.observations).find((o:any)=>o.id===f.observation_refs[0]&&(o.currency||o.kind==='reported_percent_complete'));if(financial){await expect(page.locator('.fact').filter({hasText:f.proposition})).toContainText(f.qualification);}}
 for(const answer of s.answers){await page.getByRole('button',{name:answer.question,exact:true}).click();const block=page.locator(`#answer-${answer.question_id}`);await expect(block).toBeVisible();for(const cl of answer.clauses){await expect(block).toContainText(cl.text);for(const ref of cl.finding_refs)await expect(block.getByRole('button',{name:`Evidence: ${ref}`,exact:true}).first()).toBeVisible();}}
 for(const r of s.evidence.candidates){const card=page.locator('.candidate').filter({has:page.getByRole('heading',{name:r.record_id,exact:true})});await expect(card).toContainText('POSSIBLE MATCH');await expect(card).toContainText('not admitted as facts');for(const o of r.observations){const text=o.currency?`${o.currency} ${o.value.split('.')[0].replace(/\B(?=(\d{3})+(?!\d))/g,',')}${o.value.includes('.')?'.'+o.value.split('.')[1]:''}`:o.kind==='reported_percent_complete'?o.value+'%':o.value;await expect(card).toContainText(text);}}
 for(const r of s.evidence.excluded){await expect(page.locator('#excluded').locator('..')).toContainText(r.observation.value);await expect(page.locator('#excluded').locator('..')).toContainText(r.exclusion.reason);}
 await page.getByRole('button',{name:'View evidence',exact:true}).first().click();await expect(page.getByRole('dialog')).toBeVisible();await expect(page.getByRole('dialog')).toContainText('Raw value');await expect(page.getByRole('dialog')).toContainText('Source field');
 if(id==='C01')await page.screenshot({path:path.join(evidence,'provenance.png')});await page.getByRole('button',{name:'Close evidence drawer'}).click();
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Download verification JSON'}).click();const download=await downloadPromise;const saved=path.join(evidence,`${id}.verification.json`);await download.saveAs(saved);expect(fs.readFileSync(saved).equals(original)).toBe(true);
 await page.screenshot({path:path.join(evidence,`${id}-dossier.png`),fullPage:true});
 // Active external request is blocked in this same browser context.
 expect(await page.evaluate(async()=>{try{await fetch('https://offline-check.invalid/probe');return false;}catch{return true;}})).toBe(true);
});
test('U03 keyboard drawer focus mobile caveats and headings',async({page})=>{
 await page.goto('/projects/C01/');const opener=page.getByRole('button',{name:'View evidence',exact:true}).first();await opener.focus();await page.keyboard.press('Enter');await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(opener).toBeFocused();
 await page.setViewportSize({width:390,height:844});await expect(page.locator('.review-note')).toBeVisible();await expect(page.locator('.fact').filter({hasText:'Amount certified'}).first()).toContainText('not independently verified treasury payment');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await page.screenshot({path:path.join(evidence,'mobile.png'),fullPage:true});
 await expect(page.getByRole('heading',{level:1})).toHaveCount(1);await expect(page.locator('.state').first()).toContainText('SUPPORTED');
});
test('Completion answers disclose only their admitted evidence context',async({page})=>{
 for(const id of ids){
  const s=JSON.parse(fs.readFileSync(path.join(root,`data/artifacts/${id}.json`),'utf8')).semantic;
  const f=s.findings.find((f:any)=>f.id==='completion');
  const admitted=s.evidence.accepted.flatMap((r:any)=>r.observations);
  const progress=f.observation_refs.map((ref:string)=>admitted.find((o:any)=>o.id===ref));
  expect(progress.every((o:any)=>o?.kind==='reported_percent_complete')).toBe(true);
  await page.goto(`/projects/${id}/`);
  await page.getByRole('button',{name:'Was this project completed?',exact:true}).click();
  const answer=page.locator('#answer-completed');
  if(progress.length){await expect(answer).toContainText('Historical reported progress');}
  else {await expect(answer).not.toContainText('Historical reported progress');await expect(answer).toContainText('No qualifying admitted completion evidence');}
  await answer.getByRole('button',{name:'Evidence: completion',exact:true}).click();
  await expect(page.getByRole('dialog')).toContainText('The project was completed.');
  await expect(page.getByRole('dialog')).toContainText('UNVERIFIABLE');
  await page.keyboard.press('Escape');
 }
});
test('U05 unavailable original source retains local provenance',async({page,context})=>{
 await page.goto('/projects/C01/');await page.getByRole('button',{name:'View evidence',exact:true}).first().click();const popupPromise=context.waitForEvent('page');await page.getByRole('link',{name:'Original source'}).first().click();const popup=await popupPromise;await popup.waitForLoadState().catch(()=>{});await expect(page.getByRole('dialog')).toContainText('Raw value');await expect(page.getByRole('dialog')).toContainText('local record and its provenance remain available');await popup.close();
});
for(const mode of ['missing','corrupt','stale','wrong-project','self-rehashed'])test(`U06 ${mode} artifact fails closed`,async({page})=>{
 await page.route('**/data/C01.json',route=>mode==='missing'?route.fulfill({status:404,body:'missing'}):route.fulfill({status:200,body:mode==='corrupt'?'{broken':runtimeProbe(mode)}));
 await page.goto('/projects/C01/');await expect(page.getByRole('heading',{name:'Evidence unavailable in this build'})).toBeVisible();await expect(page.locator('.dimension')).toHaveCount(0);await expect(page.locator('.fact')).toHaveCount(0);await expect(page.getByRole('button',{name:'Download verification JSON'})).toHaveCount(0);
});

// Memory-only negative cases, never persisted as demonstration records.
function runtimeProbe(mode:string){
 const artifact=JSON.parse(fs.readFileSync(path.join(root,`data/artifacts/${mode==='wrong-project'?'C02':'C01'}.json`),'utf8'));
 if(mode==='stale')artifact.semantic.hashes.rules_sha256='0'.repeat(64);
 if(mode==='self-rehashed')artifact.semantic.answers[2].clauses[0].text='Test-only unsupported completion claim';
 const canonical=(v:any):string=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(canonical).join(',')+']':'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
 artifact.semantic_sha256=createHash('sha256').update(canonical(artifact.semantic)).digest('hex');
 return canonical(artifact)+'\n';
}
