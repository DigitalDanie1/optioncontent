import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const mode=process.argv[2]||'preview';
if(!['preview','send','check','draft'].includes(mode)) throw Error('Use preview, check, draft or send');
const config=JSON.parse(await fs.readFile(path.join(root,'publish/telegram.json'),'utf8'));
async function asset(name){
 const target=path.resolve(root,name);
 if(!target.startsWith(root+path.sep))throw Error('Content path must stay in repository');
 return fs.readFile(target);
}
const text=(await asset(config.text)).toString('utf8').trim();
const photo=await asset(config.photo);
if(!text||text.length>4096)throw Error('Text must contain 1–4096 UTF-16 units');
if(!config.caption||config.caption.length>1024)throw Error('Caption must contain 1–1024 UTF-16 units');
if(photo.length>10*1024*1024||photo.toString('hex',0,8)!=='89504e470d0a1a0a')throw Error('Photo must be a PNG smaller than 10 MB');
const width=photo.readUInt32BE(16),height=photo.readUInt32BE(20);
if(width+height>10000||Math.max(width/height,height/width)>20)throw Error('Photo dimensions exceed Telegram limits');
const eligible=config.approved===true&&Number.isFinite(Date.parse(config.validUntil))&&Date.now()<=Date.parse(config.validUntil);
console.log(JSON.stringify({id:config.id,approved:config.approved,validUntil:config.validUntil,eligible,textLength:text.length,photo:[width,height],steps:['Korean one-pager photo','Korean full text']},null,2));
if(mode==='preview'){console.log('Preview only. No Telegram requests.');process.exit(0);}
const token=process.env.TELEGRAM_BOT_TOKEN?.trim();
let chat=process.env.TELEGRAM_CHAT_ID?.trim();
if(!token||!chat)throw Error('Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in GitHub Actions secrets');
if(!/^\d+:[A-Za-z0-9_-]{20,}$/.test(token))throw Error('TELEGRAM_BOT_TOKEN format invalid: store only the BotFather token (digits:letters), without the instruction text or quotes');
async function api(method,body){
 let response;
 try{response=await fetch(`https://api.telegram.org/bot${token}/${method}`,{method:'POST',body,signal:AbortSignal.timeout(60000)});}catch{throw Error(`Telegram ${method}: transport failed; do not blindly retry a send`);}
 let data;try{data=await response.json();}catch{throw Error(`Telegram ${method}: non-JSON response (HTTP ${response.status}); verify the BotFather token`);}
 if(!response.ok||!data.ok)throw Error(`Telegram ${method} failed (HTTP ${response.status}, code ${data.error_code||'unknown'}). Check token, channel and posting permission.`);
 return data.result;
}
const form=values=>{const f=new FormData();for(const[k,v]of Object.entries(values))f.set(k,String(v));return f;};
const me=await api('getMe',new URLSearchParams());
let channel=await api('getChat',form({chat_id:chat}));
if(channel.type!=='channel')throw Error('Destination must be a Telegram announcement channel');
const member=await api('getChatMember',form({chat_id:chat,user_id:me.id}));
console.log(JSON.stringify({bot_username:me.username,channel_username:channel.username,bot_role:member.status,can_post_messages:member.can_post_messages===true}));
if(member.status!=='creator'&&!(member.status==='administrator'&&member.can_post_messages))throw Error('Add the bot as channel administrator with Post Messages permission');
console.log('Bot and announcement-channel posting permission verified.');
if(mode==='check')process.exit(0);
if(mode==='draft'){
 const webhook=await api('getWebhookInfo',new URLSearchParams());
 if(webhook.url)throw Error('Bot has an active webhook; private-chat discovery stopped without changing it');
 const admins=await api('getChatAdministrators',form({chat_id:chat}));
 const owners=new Set(admins.filter(a=>a.status==='creator').map(a=>a.user.id));
 const updates=await api('getUpdates',new URLSearchParams({timeout:'0',limit:'100'}));
 console.log(JSON.stringify({update_count:updates.length,update_types:updates.map(u=>Object.keys(u).filter(k=>k!=='update_id')).flat(),private_messages:updates.filter(u=>u.message?.chat?.type==='private').length,owner_private_messages:updates.filter(u=>u.message?.chat?.type==='private'&&owners.has(u.message.from?.id)).length,start_messages:updates.filter(u=>/^\/start(?:@\w+)?(?:\s|$)/.test(u.message?.text||'')).length,owner_count:owners.size}));
 const starts=updates.map(u=>u.message).filter(m=>m?.chat?.type==='private'&&owners.has(m.from?.id)&&/^\/start(?:@\w+)?(?:\s|$)/.test(m.text||''));
 const privateIds=[...new Set(starts.map(m=>m.chat.id))];
 if(privateIds.length!==1)throw Error('PRIVATE_START_REQUIRED: send /start to this bot from the announcement-channel owner account, then retry');
 chat=String(privateIds[0]);
 channel=await api('getChat',form({chat_id:chat}));
 if(channel.type!=='private')throw Error('Draft destination must be private');
 console.log('Verified private chat belongs to the announcement-channel owner. Draft will not go to the channel.');
 if(!Number.isFinite(Date.parse(config.validUntil))||Date.now()>Date.parse(config.validUntil))throw Error('Draft expired; renew the preview expiry');
}else if(!eligible)throw Error('Publication blocked: approve a current episode and set a valid expiry first');
const stateDir=process.env.TELEGRAM_STATE_DIR;
if(!stateDir)throw Error('TELEGRAM_STATE_DIR must point to the persistent telegram-state Git checkout');
const stateFile=path.join(stateDir,'telegram-receipts.json');
let receipts={};try{receipts=JSON.parse(await fs.readFile(stateFile,'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
const targetHash=crypto.createHash('sha256').update(String(channel.id)).digest('hex').slice(0,16);
const key=`${targetHash}:${config.id}`;
const digest=crypto.createHash('sha256').update(text).update(photo).update(config.caption).digest('hex');
let receipt=receipts[key];
if(receipt&&receipt.digest!==digest)throw Error('Episode already started with different content; use a new episode ID for a new publication');
if(!receipt)receipt=receipts[key]={digest,steps:{}};
async function persist(){
 await fs.writeFile(stateFile,JSON.stringify(receipts,null,2)+'\n');
 for(const args of [['add','telegram-receipts.json'],['commit','-m',`Record Telegram publication ${config.id}`],['push','origin','HEAD:telegram-state']]){
  try{execFileSync('git',args,{cwd:stateDir,stdio:'pipe'});}catch{throw Error('Failed to persist publication receipt; stopped to avoid duplicate sends');}
 }
}
for(const step of ['photo','text']){
 const previous=receipt.steps[step];
 if(previous?.status==='sent'){console.log(`${step}: already sent; skipped`);continue;}
 if(previous)throw Error(`${step}: prior attempt is uncertain. Check channel and reconcile the receipt before retrying.`);
 receipt.steps[step]={status:'sending',at:new Date().toISOString()};await persist();
 const payload=step==='photo'?form({chat_id:chat,caption:config.caption}):form({chat_id:chat,text,link_preview_options:JSON.stringify({is_disabled:true})});
 if(step==='photo')payload.set('photo',new Blob([photo],{type:'image/png'}),path.basename(config.photo));
 const result=await api(step==='photo'?'sendPhoto':'sendMessage',payload);
 receipt.steps[step]={status:'sent',message_id:result.message_id,at:new Date().toISOString()};await persist();
 console.log(`${step}: sent`);
}
