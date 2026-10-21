import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync,spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
test('Telegram preview, stale guard, delivery receipts and duplicate suppression without network',()=>{
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'options-telegram-test-'));
 try{
  const fixture=path.join(tmp,'content'),state=path.join(tmp,'state'),remote=path.join(tmp,'remote.git');
  fs.mkdirSync(path.join(fixture,'scripts'),{recursive:true});fs.mkdirSync(path.join(fixture,'publish'));fs.mkdirSync(state);
  fs.copyFileSync(path.join(root,'scripts/telegram-publish.mjs'),path.join(fixture,'scripts/telegram-publish.mjs'));
  fs.copyFileSync(path.join(root,'assets/images/weekly-options-W42-ko.png'),path.join(fixture,'photo.png'));fs.writeFileSync(path.join(fixture,'text.txt'),'테스트 원고');
  const config={id:'test',approved:false,validUntil:'2099-01-01',text:'text.txt',photo:'photo.png',caption:'테스트'};
  const write=()=>fs.writeFileSync(path.join(fixture,'publish/telegram.json'),JSON.stringify(config));write();
  const mock=path.join(tmp,'mock.mjs'),log=path.join(tmp,'calls.txt');
  fs.writeFileSync(mock,`import fs from 'node:fs';globalThis.fetch=async(url,options)=>{const method=new URL(url).pathname.split('/').at(-1);fs.appendFileSync(process.env.TEST_CALLS,method+'\\n');if(process.env.TEST_FAIL===method)throw Error('simulated timeout');const result=method==='getMe'?{id:1}:method==='getChat'?(options.body.get('chat_id')==='1001'?{id:1001,type:'private'}:{id:-100123,type:'channel'}):method==='getWebhookInfo'?{}:method==='getChatAdministrators'?[{status:'creator',user:{id:1001}}]:method==='getUpdates'?[{message:{chat:{id:1001,type:'private'},from:{id:1001},text:'/start'}}]:method==='getChatMember'?{status:'administrator',can_post_messages:true}:{message_id:42};return {ok:true,status:200,json:async()=>({ok:true,result})};};`);
  const git=(args,cwd=state)=>execFileSync('git',args,{cwd,stdio:'pipe'});
  git(['init','--bare',remote],tmp);git(['init']);git(['config','user.name','Test']);git(['config','user.email','test@example.com']);fs.writeFileSync(path.join(state,'telegram-receipts.json'),'{}');git(['add','.']);git(['commit','-m','init']);git(['remote','add','origin',remote]);git(['push','origin','HEAD:telegram-state']);
  const run=mode=>spawnSync(process.execPath,['--import',mock,path.join(fixture,'scripts/telegram-publish.mjs'),mode],{encoding:'utf8',env:{...process.env,TELEGRAM_BOT_TOKEN:'123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi',TELEGRAM_CHAT_ID:'@mock',TELEGRAM_STATE_DIR:state,TEST_CALLS:log}});
  assert.equal(run('preview').status,0);assert.equal(fs.existsSync(log),false);
  assert.notEqual(run('send').status,0);assert(!fs.readFileSync(log,'utf8').includes('sendPhoto'));
  config.approved=true;write();let sent=run('send');assert.equal(sent.status,0,sent.stderr);
  sent=run('send');assert.equal(sent.status,0,sent.stderr);
  const calls=fs.readFileSync(log,'utf8');assert.equal(calls.split('sendPhoto').length-1,1);assert.equal(calls.split('sendMessage').length-1,1);
  config.id='private-draft';config.approved=false;write();const draft=run('draft');assert.equal(draft.status,0,draft.stderr);assert(draft.stdout.includes('Draft will not go to the channel'));assert(!fs.readFileSync(log,'utf8').includes('getUpdates'));
  config.id='uncertain';config.approved=true;write();const failed=spawnSync(process.execPath,['--import',mock,path.join(fixture,'scripts/telegram-publish.mjs'),'send'],{encoding:'utf8',env:{...process.env,TELEGRAM_BOT_TOKEN:'123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi',TELEGRAM_CHAT_ID:'@mock',TELEGRAM_STATE_DIR:state,TEST_CALLS:log,TEST_FAIL:'sendPhoto'}});assert.notEqual(failed.status,0);
  const before=fs.readFileSync(log,'utf8').split('sendPhoto').length;assert.notEqual(run('send').status,0);assert.equal(fs.readFileSync(log,'utf8').split('sendPhoto').length,before);
 }finally{fs.rmSync(tmp,{recursive:true,force:true});}
});
