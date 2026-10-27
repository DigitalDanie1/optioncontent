import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const build=JSON.parse(await fs.readFile(path.join(root,'publish/weekly-build.json'),'utf8'));
const config=JSON.parse(await fs.readFile(path.join(root,'publish/telegram.json'),'utf8'));
if(build.configId!==config.id)throw Error('Build/config mismatch');
const browser=await chromium.launch(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{});
try{
 const page=await browser.newPage({viewport:{width:2880,height:1620},deviceScaleFactor:1});
 for(const lang of ['ko','en']){
  await page.goto(pathToFileURL(path.join(root,`scripts/current-${lang}.html`)).href);
  await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()));});
  const overlap=await page.evaluate(()=>[...document.querySelectorAll('.cols section')].some(e=>e.getBoundingClientRect().bottom>document.querySelector('footer').getBoundingClientRect().top-10));
  if(overlap)throw Error('Poster footer overlap: '+lang);
  await page.locator('.card').screenshot({path:path.join(root,lang==='ko'?build.photo:build.englishPhoto)});
 }
 await page.setViewportSize({width:390,height:844});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(root,'studio.html')).href);
 await page.waitForSelector('.tweet-card',{state:'attached'});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile studio overflow');
 if(errors.length)throw Error(errors.join(';'));
 const digest={};for(const file of [build.text,build.photo,build.englishPhoto,build.englishText])digest[file]=crypto.createHash('sha256').update(await fs.readFile(path.join(root,file))).digest('hex');
 await fs.writeFile(path.join(root,'publish/weekly-ready.json'),JSON.stringify({...build,preparedAt:new Date().toISOString(),hashes:digest,validated:true},null,2)+'\n');
 console.log('Ready:',build.configId,'Korean/English posters, mobile studio and file hashes verified.');
}finally{await browser.close();}
