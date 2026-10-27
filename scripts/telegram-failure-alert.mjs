// Failure notification only; never sends to the public channel.
const token=process.env.TELEGRAM_BOT_TOKEN?.trim(),chat=process.env.TELEGRAM_CHAT_ID?.trim();
if(!token||!chat)throw Error('Missing Telegram connection');
async function api(method,fields){let r;try{r=await fetch(`https://api.telegram.org/bot${token}/${method}`,{method:'POST',body:new URLSearchParams(fields),signal:AbortSignal.timeout(30000)});}catch{throw Error('Telegram connection failed');}let d;try{d=await r.json();}catch{throw Error('Telegram returned unreadable response');}if(!d.ok)throw Error('Telegram request failed');return d.result;}
const admins=await api('getChatAdministrators',{chat_id:chat});const owners=admins.filter(a=>a.status==='creator');if(owners.length!==1)throw Error('Owner identity ambiguous');const id=String(owners[0].user.id);const person=await api('getChat',{chat_id:id});if(person.type!=='private')throw Error('Not a private chat');
const url=`https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`;
await api('sendMessage',{chat_id:id,text:`⚠️ 주간 옵션 콘텐츠 작업이 완료되지 않았습니다.\n\n오래된 회차는 대신 보내지 않았습니다. 준비·검증·전송 중 실패한 단계는 아래 실행 기록에서 확인할 수 있습니다.\n${url}`,link_preview_options:JSON.stringify({is_disabled:true})});
console.log('Failure notice sent to owner private chat.');
