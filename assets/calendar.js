(()=>{
'use strict';
const $=id=>document.getElementById(id),KEY='defidaniel-content-calendar-v1';
const channels=['텔레그램','X','봇 미리보기'],formats=['글','원페이저','영상'],statuses=['기획','제작중','검토대기','게시예정','게시완료'];
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Singapore',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const parse=s=>{const[y,m,d]=s.split('-').map(Number);return new Date(y,m-1,d,12);};
const key=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const dateLabel=s=>new Intl.DateTimeFormat('ko-KR',{month:'long',day:'numeric',weekday:'short'}).format(parse(s));
function validEvent(e){return e&&typeof e.id==='string'&&e.id.length<=150&&typeof e.title==='string'&&e.title.trim().length>0&&e.title.length<=100&&/^\d{4}-\d{2}-\d{2}$/.test(e.date)&&key(parse(e.date))===e.date&&/^([01]\d|2[0-3]):[0-5]\d$/.test(e.time)&&channels.includes(e.channel)&&statuses.includes(e.status)&&Array.isArray(e.formats)&&e.formats.length>0&&e.formats.every(f=>formats.includes(f))&&typeof e.note==='string'&&e.note.length<=1000&&typeof e.link==='string'&&(!e.link||/^https?:\/\//i.test(e.link));}
let events=JSON.parse($('calendar-seed').textContent),selected=today,month=parse(today),view=matchMedia('(max-width:760px)').matches?'list':'month';
try{const saved=JSON.parse(localStorage.getItem(KEY));if(Array.isArray(saved)&&saved.every(validEvent))events=saved;}catch{}
let toastTimer;
function toast(t){$('calendarToast').textContent=t;$('calendarToast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('calendarToast').hidden=true,3500);}
function save(){try{localStorage.setItem(KEY,JSON.stringify(events));return true;}catch{toast('저장 공간이 부족하거나 저장이 차단됐어요. 일정을 내보내 주세요.');return false;}}
const sort=(a,b)=>(a.date+a.time).localeCompare(b.date+b.time)||a.title.localeCompare(b.title);
const matches=e=>(!$('channelFilter').value||e.channel===$('channelFilter').value)&&(!$('formatFilter').value||e.formats.includes($('formatFilter').value));
const stateClass=e=>e.status==='게시완료'?'done':e.status==='게시예정'?'scheduled':'plan';
function render(){
 const y=month.getFullYear(),m=month.getMonth(),monthKey=`${y}-${String(m+1).padStart(2,'0')}`;
 $('monthTitle').textContent=`${y}년 ${m+1}월`;
 const all=events.filter(e=>e.date.startsWith(monthKey)&&matches(e)).sort(sort);
 $('totalStat').textContent=all.length;$('doneStat').textContent=all.filter(e=>e.status==='게시완료').length;$('scheduledStat').textContent=all.filter(e=>e.status==='게시예정').length;$('pendingStat').textContent=all.filter(e=>!['게시완료','게시예정'].includes(e.status)).length;
 const first=new Date(y,m,1,12),start=new Date(y,m,1-first.getDay(),12),cells=Math.ceil((first.getDay()+new Date(y,m+1,0).getDate())/7)*7;
 let html='<div class="weekdays">'+['일','월','화','수','목','금','토'].map(d=>`<span>${d}</span>`).join('')+'</div><div class="month-grid">';
 for(let i=0;i<cells;i++){
  const d=new Date(start);d.setDate(d.getDate()+i);const date=key(d),items=events.filter(e=>e.date===date&&matches(e)).sort(sort);
  html+=`<div class="day ${d.getMonth()!==m?'outside':''} ${date===selected?'selected':''} ${date===today?'is-today':''}" data-date="${date}" role="button" tabindex="0" aria-label="${escape(dateLabel(date))}, 일정 ${items.length}개" aria-pressed="${date===selected}"><span class="day-number">${d.getDate()}</span>${items.slice(0,2).map(e=>`<button class="event-chip ${stateClass(e)}" data-edit="${escape(e.id)}" title="${escape(e.title)}"><small>${e.time} · ${escape(e.channel)}</small><span class="event-name">${escape(e.title)}</span></button>`).join('')}${items.length>2?`<div class="more">+${items.length-2}개 더 보기</div>`:''}</div>`;
 }
 $('calendar').innerHTML=html+'</div>';
 const dates=[...new Set(all.map(e=>e.date))];
 $('agenda').innerHTML=dates.length?dates.map(date=>`<div class="agenda-group"><h3>${escape(dateLabel(date))}${date===today?' · 오늘':''}</h3>${all.filter(e=>e.date===date).map(e=>`<button class="agenda-event" data-select="${date}"><span><small>${e.time} · ${escape(e.channel)} · ${escape(e.formats.join(' + '))}</small><strong>${escape(e.title)}</strong></span><span class="status ${stateClass(e)}">${e.status}</span></button>`).join('')}</div>`).join(''):'<div class="empty"><b>등록된 일정이 없어요</b>날짜를 선택해 첫 콘텐츠를 계획해 보세요.<br><button id="emptyAdd" style="margin-top:16px">＋ 일정 추가</button></div>';
 $('calendar').hidden=view!=='month';$('agenda').hidden=view!=='list';$('monthView').setAttribute('aria-pressed',String(view==='month'));$('listView').setAttribute('aria-pressed',String(view==='list'));
 renderDay();
}
function renderDay(){
 const items=events.filter(e=>e.date===selected&&matches(e)).sort(sort);
 $('selectedTitle').textContent=dateLabel(selected);$('selectedCount').textContent=`${selected===today?'오늘 · ':''}콘텐츠 ${items.length}개`;
 $('dayItems').innerHTML=items.length?items.map(e=>`<article class="day-card"><div class="time-line"><time>${e.time} SGT</time><span class="status ${stateClass(e)}">${e.status}</span></div><h3>${escape(e.title)}</h3><div class="tags">${escape(e.channel)} · ${escape(e.formats.join(' + '))}</div>${e.note?`<p>${escape(e.note)}</p>`:''}<div class="card-actions"><button data-edit="${escape(e.id)}">수정</button>${e.link?`<a href="${escape(e.link)}" target="_blank" rel="noopener noreferrer">게시물·작업 보기 ↗</a>`:''}</div></article>`).join(''):'<div class="empty"><b>아직 비어 있는 하루</b>다음 옵션 콘텐츠를 계획해 보세요.</div>';
}
function selectDate(date){selected=date;month=parse(date);render();}
function openForm(id){
 const e=events.find(e=>e.id===id);$('eventForm').reset();$('eventId').value=e?.id||'';$('dialogTitle').textContent=e?'일정 수정':'일정 추가';$('eventTitle').value=e?.title||'';$('eventDate').value=e?.date||selected;$('eventTime').value=e?.time||'21:00';$('eventChannel').value=e?.channel||'텔레그램';$('eventStatus').value=e?.status||'기획';$('eventLink').value=e?.link||'';$('eventNote').value=e?.note||'';
 document.querySelectorAll('input[name=format]').forEach(c=>c.checked=(e?.formats||['글']).includes(c.value));$('deleteEvent').hidden=!e;$('eventDialog').showModal();$('eventTitle').focus();
}
$('eventForm').addEventListener('submit',e=>{e.preventDefault();const id=$('eventId').value;const item={id:id||globalThis.crypto?.randomUUID?.()||`${Date.now()}-${Math.random().toString(36).slice(2)}`,title:$('eventTitle').value.trim(),date:$('eventDate').value,time:$('eventTime').value,channel:$('eventChannel').value,status:$('eventStatus').value,formats:[...document.querySelectorAll('input[name=format]:checked')].map(c=>c.value),link:$('eventLink').value.trim(),note:$('eventNote').value.trim()};
 if(!validEvent(item)){toast('제목·날짜·시간과 콘텐츠 형식을 확인해 주세요.');return;}
 const index=events.findIndex(e=>e.id===id);if(index>=0)events[index]=item;else events.push(item);const stored=save();$('eventDialog').close();selectDate(item.date);if(stored)toast('일정을 저장했어요. 자동 발송은 하지 않습니다.');
});
$('deleteEvent').onclick=()=>{const id=$('eventId').value;if(!id||!confirm('이 일정을 삭제할까요? 실제 게시물은 삭제되지 않습니다.'))return;events=events.filter(e=>e.id!==id);save();$('eventDialog').close();render();};
$('closeDialog').onclick=()=>$('eventDialog').close();$('addTop').onclick=$('addDay').onclick=()=>openForm();
$('prev').onclick=()=>{month=new Date(month.getFullYear(),month.getMonth()-1,1,12);render();};$('next').onclick=()=>{month=new Date(month.getFullYear(),month.getMonth()+1,1,12);render();};$('today').onclick=()=>selectDate(today);
$('monthView').onclick=()=>{view='month';render();};$('listView').onclick=()=>{view='list';render();};$('channelFilter').onchange=$('formatFilter').onchange=render;
function handleClick(e){const edit=e.target.closest('[data-edit]');if(edit){openForm(edit.dataset.edit);return;}const select=e.target.closest('[data-select],[data-date]');if(select){selectDate(select.dataset.select||select.dataset.date);return;}if(e.target.closest('#emptyAdd'))openForm();}
$('calendar').onclick=$('agenda').onclick=$('dayItems').onclick=handleClick;
$('calendar').onkeydown=e=>{if(e.target.matches('.day')&&['Enter',' '].includes(e.key)){e.preventDefault();selectDate(e.target.dataset.date);}};
$('export').onclick=()=>{const blob=new Blob([JSON.stringify({version:1,timezone:'Asia/Singapore',events},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`defidaniel-calendar-${today}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('import').onclick=()=>$('importFile').click();$('importFile').onchange=async()=>{const file=$('importFile').files[0];if(!file)return;try{if(file.size>2e6)throw Error();const data=JSON.parse(await file.text()),rows=Array.isArray(data)?data:data.events;if(!Array.isArray(rows)||rows.length>5000||!rows.every(validEvent)||new Set(rows.map(e=>e.id)).size!==rows.length)throw Error();if(!confirm(`현재 일정을 불러온 ${rows.length}개 일정으로 바꿀까요?`))return;events=rows;save();render();toast('일정을 불러왔어요.');}catch{toast('올바른 일정 JSON 파일인지 확인해 주세요.');}finally{$('importFile').value='';}};
render();
})();
