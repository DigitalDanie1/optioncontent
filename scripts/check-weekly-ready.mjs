import fs from 'node:fs/promises';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const c=JSON.parse(await fs.readFile(path.join(root,'publish/telegram.json'),'utf8'));
const r=JSON.parse(await fs.readFile(path.join(root,'publish/weekly-ready.json'),'utf8'));
const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Singapore',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
if(!Number.isFinite(Date.parse(r.preparedAt))||!Number.isFinite(Date.parse(r.snapshotAt))||Date.now()-Date.parse(r.snapshotAt)>72*3600000||!r.validated||r.configId!==c.id||r.deliveryDate!==today||Date.now()-Date.parse(r.preparedAt)>72*3600000||Date.parse(r.preparedAt)>Date.now()+60000||Date.now()>Date.parse(c.validUntil))throw Error('Weekly review is missing, stale, expired or for another delivery date');
if(r.text!==c.text||r.photo!==c.photo||!r.hashes?.[c.text]||!r.hashes?.[c.photo])throw Error('Missing or mismatched ready assets');
for(const[file,expected]of Object.entries(r.hashes)){const p=path.resolve(root,file);if(!p.startsWith(root+path.sep))throw Error('Invalid path');const digest=crypto.createHash('sha256').update(await fs.readFile(p)).digest('hex');if(digest!==expected)throw Error('Asset changed after validation: '+file);}
console.log('PASS ready for private draft:',c.id,today);
