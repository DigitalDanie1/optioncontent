import {test} from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';import os from 'node:os';import crypto from 'node:crypto';import {spawnSync} from 'node:child_process';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
test('Delivery guard rejects stale dates, changed assets, invalid clocks and missing readiness',()=>{
 const t=fs.mkdtempSync(path.join(os.tmpdir(),'weekly-ready-'));
 try{
  fs.mkdirSync(path.join(t,'scripts'));fs.mkdirSync(path.join(t,'publish'));fs.copyFileSync(path.join(root,'scripts/check-weekly-ready.mjs'),path.join(t,'scripts/check-weekly-ready.mjs'));
  const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Singapore',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  fs.writeFileSync(path.join(t,'text.txt'),'new review');fs.writeFileSync(path.join(t,'photo.png'),'image');
  const hashes=Object.fromEntries(['text.txt','photo.png'].map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(path.join(t,p))).digest('hex')]));
  const c={id:'new',text:'text.txt',photo:'photo.png',validUntil:new Date(Date.now()+3600000).toISOString()};const r={validated:true,configId:'new',deliveryDate:today,preparedAt:new Date().toISOString(),snapshotAt:new Date().toISOString(),text:c.text,photo:c.photo,hashes};
  fs.writeFileSync(path.join(t,'publish/telegram.json'),JSON.stringify(c));
  const write=()=>fs.writeFileSync(path.join(t,'publish/weekly-ready.json'),JSON.stringify(r));
  const run=()=>spawnSync(process.execPath,[path.join(t,'scripts/check-weekly-ready.mjs')],{encoding:'utf8'}).status;
  assert.notEqual(run(),0);write();assert.equal(run(),0);
  r.deliveryDate='2000-01-01';write();assert.notEqual(run(),0);r.deliveryDate=today;
  r.preparedAt='invalid';write();assert.notEqual(run(),0);r.preparedAt=new Date().toISOString();
  r.snapshotAt=new Date(Date.now()-80*3600000).toISOString();write();assert.notEqual(run(),0);r.snapshotAt=new Date().toISOString();write();
  fs.writeFileSync(path.join(t,'text.txt'),'changed after validation');assert.notEqual(run(),0);
 }finally{fs.rmSync(t,{recursive:true,force:true});}
});
