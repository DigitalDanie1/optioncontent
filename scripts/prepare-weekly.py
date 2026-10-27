"""Build a dated, source-backed options review. No private credentials or publishing."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import json, urllib.request, ssl, hashlib, html, re, sys
ROOT=Path(__file__).resolve().parents[1];SGT=ZoneInfo('Asia/Singapore');now=datetime.now(timezone.utc);local=now.astimezone(SGT);day=local.date();stamp=day.isoformat();iso=day.isocalendar();week=f'{iso.year}-W{iso.week:02d}';cid=f'{week}-review-{stamp}';folder=ROOT/'sources/weekly'/stamp;folder.mkdir(parents=True,exist_ok=True)
ctx=ssl.create_default_context()
try:
 import certifi
 ctx=ssl.create_default_context(cafile=certifi.where())
except ImportError: pass

def write(p,obj):
 p=ROOT/p if not isinstance(p,Path) else p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'defidaniel-options-review/1.0'})
 with urllib.request.urlopen(req,timeout=40,context=ctx) as r:return r.read().decode()
def money(n):return '미집계' if not isinstance(n,(int,float)) else f'${n/1e6:.2f}M' if n>=1e6 else f'${n:,.0f}'
def price(n):return f'${n:.8f}'.rstrip('0').rstrip('.') if isinstance(n,(int,float)) else 'N/A'
def safe(s):return html.escape(str(s),quote=True)
raw=fetch('https://opshnz.com/');i=raw.index('const BOOT = ')+len('const BOOT = ');boot=json.JSONDecoder().raw_decode(raw[i:])[0];snap=boot['snapshot'];at=datetime.fromisoformat(snap['at'].replace('Z','+00:00'));age=now-at
if age>timedelta(hours=72) or age<timedelta(minutes=-15):raise SystemExit('OPSHNZ snapshot is stale or future-dated; no ready record created')
write(folder/'opshnz.json',boot);sourceTime=at.astimezone(SGT).strftime('%m/%d %H:%M SGT');projects={p['name']:p for p in snap['projects']};news=[];events=[];limits=[]
editor=json.loads((ROOT/'publish/editorial.json').read_text())
for n in editor['news']:
 try:
  published=datetime.fromisoformat(n['date']).date()
  if not day-timedelta(days=7)<=published<=day:continue
  page=fetch(n['url']);soup=BeautifulSoup(page,'html.parser');body=soup.get_text(' ',strip=True)
  if n['verify'].lower() not in body.lower():raise ValueError('source verification phrase missing')
  (folder/(n['project'].lower()+'-official.html')).write_text(page);news.append(n)
 except Exception as e:limits.append(f"Official news {n['project']} unavailable: {type(e).__name__}")
for e in editor['events']:
 if day<=datetime.fromisoformat(e['endDate']).date()<=day+timedelta(days=7):
  try:
   page=fetch(e['url']);body=BeautifulSoup(page,'html.parser').get_text(' ',strip=True)
   if e['verify'] not in body or '2026' not in body:raise ValueError('event not verified')
   (folder/'macro-official.html').write_text(page);events.append(e)
  except Exception as err:limits.append('Macro event confirmation unavailable: '+type(err).__name__)
# Active public spot pairs: no assumption based on old listing articles.
audit={}
for venue,url in [('Coinbase','https://api.exchange.coinbase.com/products'),('Gate','https://api.gateio.ws/api/v4/spot/currency_pairs'),('Binance','https://api.binance.com/api/v3/exchangeInfo')]:
 try:
  data=json.loads(fetch(url));write(folder/(venue.lower()+'-spot.json'),data)
  if venue=='Coinbase':pairs={r['base_currency'] for r in data if r.get('status')=='online' and not r.get('trading_disabled')}
  elif venue=='Gate':pairs={r['base'] for r in data if r.get('trade_status')=='tradable'}
  else:pairs={r['baseAsset'] for r in data['symbols'] if r.get('status')=='TRADING' and r.get('isSpotTradingAllowed',True)}
  audit[venue]=sorted(pairs&{'DRV','AEVO','NUTS','SYN'})
 except Exception as e:limits.append(f'{venue} spot check unavailable: {type(e).__name__}')
write(folder/'spot-audit.json',{'checkedAt':now.isoformat(),'venues':audit,'limits':limits})
focus=[projects[n] for n in ['Derive','Aevo','Thetanuts','Hypercall'] if n in projects]
pre=[projects[n] for n in ['CallPut','Rysk','Dream'] if n in projects]
dm=snap.get('dm',{});btc=dm.get('assets',{}).get('BTC',{});dmAt=datetime.fromtimestamp(dm['at']/1000,timezone.utc) if dm.get('at') else at
if now-dmAt>timedelta(hours=72):btc={};limits.append('Strategy metrics older than 72 hours; excluded')
iv=btc.get('iv30');rv=btc.get('rv',{}).get('value');metric=f'BTC 30D IV {iv:.2f}% / RV {rv:.2f}%' if iv is not None and rv is not None else 'BTC IV/RV: current measurement unavailable'
metricAt=dmAt.astimezone(SGT).strftime('%m/%d %H:%M SGT')
newsKo='\n\n'.join(f"{n['project']} · {n['date'][5:]}\n{n['ko']}\n{n['url']}" for n in news) or '최근 7일 새 공식 발표를 직접 확인하지 못했습니다. 아래 수치 갱신을 신규 출시로 해석하지 않습니다.'
projectKo=[]
for p in focus:
 venues=[v for v,ts in audit.items() if p['ticker'] in ts]
 projectKo.append(f"• {p['name']} · {p['ticker']} {price(p.get('price'))}\n  옵션 명목 거래량 7D {money(p.get('vol7'))} · 현물 {', '.join(venues) if venues else '재확인 미완료'}")
macroKo='\n'.join('• '+e['ko']+'\n'+e['url'] for e in events) or '향후 7일 공식 일정 확인 범위가 제한돼 특정 발표 시각·예상치를 싣지 않습니다.'
text=f'''주간 온체인 옵션 돌아보기 · {week}
자료 확인 {stamp} / 지표 {sourceTime}

【1부】주간 온체인

{newsKo}

토큰 프로젝트 · 데이터 업데이트
{chr(10).join(projectKo)}

Pre-TGE 관찰
{chr(10).join('• '+p['name']+': 7D '+money(p.get('vol7')) for p in pre)}
※ 미집계는 0이 아닙니다. Pre-TGE는 토큰·에어드롭 확정이 아닙니다. 현물 확인 범위는 이번에 응답한 거래소 API만 포함합니다.

【2부】트레이딩 뷰

기본 판단: 관망, 새 호가 확인 우선
{metric}
기준 {metricAt} · OPSHNZ 집계.
과거 실현 변동성과 IV 비교만으로 매도 우위나 방향을 단정하지 않습니다.

조건부 학습 사례: 베어 풋 스프레드
행사가 100 풋 매수 / 95 풋 매도.
순비용 2를 가정한 설명용 예시이며 실제 호가·BTC 달러 가격이 아닙니다.

만기 가격 ≤95 → 최대 이익 +3
만기 가격 98 → 손익 0
만기 가격 ≥100 → 최대 손실 −2
수수료·슬리피지 제외. 만기 전 손익은 다릅니다.

SWOT
S 손실 상한·단독 풋 대비 비용 절감
W 시간가치 소모·하락 이익 상한
O 실제 하방 이탈·회복 실패 확인 시 재검토
T 반등·IV 하락·두 다리 체결 위험

【3부】매크로 뷰

{macroKo}

확인된 일정과 방향성 전망은 다릅니다.
정책 결과 → 금리·달러 반응 → BTC 가격·IV·풋 스큐 순서로 확인합니다. 금리 하락만으로 상승을 단정하지 않습니다.

원페이저·근거: https://optioncontent.vercel.app/studio.html
옵션 하면, defidaniel.'''
if len(text)>4000:raise SystemExit('Mobile copy too long')
tweets=[f'Onchain Options Weekly | {week}\n\nMetrics as of {sourceTime}. Source-backed project review, conditional strategy education and macro watch.\n\nOptions, every week — defidaniel.',*[f"{n['project']} | {n['date']}\n\n{n['en']}\n{n['url']}" for n in news],*[f"{p['name']} / {p['ticker']}\nPrice {price(p.get('price'))}\nRolling 7D options notional: {money(p.get('vol7'))}\n\nOPSHNZ snapshot: {sourceTime}. Missing volume is not zero." for p in focus],f'{metric}\nAs of {metricAt}.\n\nHistorical realised volatility is not a forecast. This comparison alone does not establish a short-volatility edge.', 'Illustrative bear put spread:\nBuy 100 put, sell 95 put, pay net 2. Same underlying/expiry, equal size.\n\nExpiry max loss 2; max profit 3; break-even 98. Not live prices. Fees/slippage excluded.', 'SWOT | Bear put spread\n\nS: capped loss, lower debit than a standalone put.\nW: theta decay, capped gain.\nO: reassess after a confirmed breakdown.\nT: rebound, IV decline, poor leg execution.']
if events:tweets.append('Macro watch | '+events[0]['en']+'\n\nWatch rates, USD, BTC and IV/skew reactions. A policy surprise is not an automatic directional signal.\n'+events[0]['url'])
# Plain URLs count as 23 weighted characters. Keep English posts under 280.
for t in tweets:
 if len(re.sub(r'https?://\S+','x'*23,t))>280:raise SystemExit('X draft exceeds 280 characters')
base=f'assets/weekly/{cid}';(ROOT/base).mkdir(parents=True,exist_ok=True);(ROOT/base/'telegram.txt').write_text(text+'\n');(ROOT/base/'x.txt').write_text('\n\n---\n\n'.join(tweets)+'\n')
# The conceptual payoff is exact: min(max(100-S,0),5)-2.
svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 320"><rect width="700" height="320" fill="#172638"/><path d="M75 190H655M75 35V265" stroke="#8d9db0" fill="none"/><path d="M75 67H275L475 238H655" stroke="#e9d0a0" stroke-width="6" fill="none"/><g fill="#dfe7ef" font-family="sans-serif" font-size="21"><text x="10" y="73">+3</text><text x="25" y="195">0</text><text x="10" y="244">−2</text><text x="258" y="297">95</text><text x="375" y="297">98</text><text x="458" y="297">100</text><text x="80" y="25">Expiry P&amp;L · illustrative units</text><text x="503" y="295">Expiry price</text></g><circle cx="395" cy="190" r="7" fill="#90cfb7"/><path d="M275 67V270M475 238V270" stroke="#6d819b" stroke-dasharray="5 7"/></svg>'''
# Correct axis placement: S95 x275,P3 y67; S100 x475,P-2 y238; P0 y169.6, S98 x395.
svg=svg.replace('190','169.6').replace('195','175')
(ROOT/base/'payoff.svg').write_text(svg)
for lang in ['ko','en']:
 ko=lang=='ko';title='주간 온체인 옵션 돌아보기' if ko else 'Onchain Options Weekly'
 newsHtml=''.join(f'<article><h3>{safe(n["project"])} <small>{n["date"][5:]}</small></h3><p>{safe(n[lang])}</p></article>' for n in news) or '<p>'+('이번 회차는 검증된 수치 업데이트 중심입니다.' if ko else 'This edition focuses on verified metric updates.')+'</p>'
 table=''.join(f'<tr><td>{safe(p["name"])} · {safe(p["ticker"])}</td><td>{price(p.get("price"))}</td><td>{money(p.get("vol7"))}</td></tr>' for p in focus)
 preHtml=''.join(f'<p>{safe(p["name"])} <b>{money(p.get("vol7"))}</b></p>' for p in pre)
 sub=['주간 온체인','트레이딩 뷰','매크로 뷰'] if ko else ['Onchain review','Trading view','Macro view']
 eventHtml=''.join(f'<article><h3>{safe(e[lang])}</h3><p>Federal Reserve · official calendar</p></article>' for e in events) or '<p>'+('새 공식 일정 직접 확인 범위 제한' if ko else 'Fresh official event verification limited')+'</p>'
 htmlDoc=f'''<!doctype html><meta charset="utf-8"><style>@font-face{{font-family:P;src:url(../assets/pretendard.woff2)}}*{{box-sizing:border-box}}body{{margin:0;color:#f2f4f7;background:#111927;font-family:P,sans-serif}}.card{{width:2880px;height:1620px;padding:0 70px 40px;overflow:hidden;position:relative}}header{{height:300px;padding:45px 0;background:linear-gradient(90deg,#111927ee,#11192777),url('../assets/images/options-cover-greeks-sg.png') center/cover;margin:0 -70px;padding-left:70px}}header span{{color:#e9d0a0;letter-spacing:5px;font-size:25px}}h1{{font-size:84px;margin:20px 0}}header p{{overflow-wrap:anywhere;font-size:27px;color:#d0d8e2}}.cols{{display:grid;grid-template-columns:1.08fr 1fr .92fr;gap:44px;margin-top:35px}}section{{min-width:0}}section+section{{padding-left:35px;border-left:1px solid #354457}}h2{{font-size:34px;color:#e9d0a0;border-bottom:2px solid #e9d0a0;padding:0 0 20px;margin:0 0 22px}}h3{{font-size:31px;margin:0 0 12px}}p{{overflow-wrap:anywhere;font-size:27px;line-height:1.6;margin:0 0 18px}}article{{padding:20px 0;border-bottom:1px solid #354457}}article:first-of-type{{padding-top:0}}small{{font-size:21px;color:#b1c0d1}}table{{width:100%;font-size:23px;border-collapse:collapse;margin:22px 0}}td{{padding:12px 5px;border-bottom:1px solid #354457}}td:not(:first-child){{text-align:right}}.box{{background:#1b2a3c;padding:25px;margin:20px 0}}.box strong{{color:#e9d0a0;font-size:38px;display:block}}.chart{{width:100%;margin:16px 0}}.swot{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.swot p{{font-size:25px;background:#1b2a3c;padding:20px}}.note{{font-size:22px;color:#b7c5d6}}.macro-flow{{padding:30px;background:#1b2a3c;font-size:32px;line-height:1.8;margin:24px 0}}footer{{position:absolute;bottom:25px;left:70px;right:70px;border-top:1px solid #354457;padding-top:15px;font-size:20px;color:#b7c5d6;display:flex;justify-content:space-between}}.mono{{font-size:25px}}.pre p{{display:flex;justify-content:space-between;font-size:25px;margin:7px 0}}</style><div class="card"><header><span>OPTIONS WEEKLY · {week} · defidaniel</span><h1>{title}</h1><p>{('확인된 데이터와 공식 발표부터' if ko else 'Start with verified data and official sources')} · {sourceTime}</p></header><div class="cols"><section><h2>01 · {sub[0]}</h2>{newsHtml}<table><tr><td>{'토큰 프로젝트' if ko else 'Token projects'}</td><td>USD</td><td>7D notional</td></tr>{table}</table><h3>Pre-TGE</h3><div class="pre">{preHtml}</div><p class="note">{'미집계 ≠ 0 · 토큰·에어드롭 확정 아님' if ko else 'N/A is not zero. No TGE or airdrop is confirmed.'}</p></section><section><h2>02 · {sub[1]}</h2><div class="box"><strong>{'관망 · 새 호가 확인 우선' if ko else 'Wait · refresh executable quotes'}</strong><p class="mono">{metric}</p><small>{metricAt} · OPSHNZ</small></div><h3>{'조건부 학습 · 베어 풋 스프레드' if ko else 'Conditional study · bear put spread'}</h3><p>{'100 풋 매수 / 95 풋 매도 · 순비용 2 가정' if ko else 'Buy 100 put / sell 95 put · assume debit 2'}</p><img class="chart" src="../{base}/payoff.svg"><p class="note">{'설명용 단위 · 실제 BTC 가격·호가 아님' if ko else 'Illustrative units, not live BTC prices or quotes'}<br>{'만기 최대 손실 2 · 최대 이익 3 · 손익분기 98' if ko else 'Expiry max loss 2 · max gain 3 · break-even 98'}</p><div class="swot"><p>S · {'손실 상한' if ko else 'Capped loss'}</p><p>W · {'시간가치 소모' if ko else 'Theta decay'}</p><p>O · {'하방 이탈 확인' if ko else 'Confirmed breakdown'}</p><p>T · {'반등·IV 하락' if ko else 'Rebound / lower IV'}</p></div><p class="note">{'IV/RV 비교만으로 매도 우위 단정 불가. 수수료·슬리피지 제외.' if ko else 'IV/RV alone does not prove a short-vol edge. Fees and slippage excluded.'}</p></section><section><h2>03 · {sub[2]}</h2>{eventHtml}<div class="macro-flow">{'정책 결과<br>↓<br>금리·달러 반응<br>↓<br>BTC 가격·IV·풋 스큐' if ko else 'Policy outcome<br>↓<br>Rates / USD reaction<br>↓<br>BTC price / IV / put skew'}</div><h3>{'확인할 것' if ko else 'What to watch'}</h3><p>{'발표 방향과 가격 반응을 구분.<br>기대 선반영·반대 반응을 확인.<br>실제 호가 없이는 진입 판단 보류.' if ko else 'Separate policy direction from price response.<br>Watch what was already priced in.<br>Do not enter without fresh quotes.'}</p><p class="note">{'전망·매수 지시가 아닌 조건부 검토본. 최신 체결 호가와 완전한 X 타임라인은 확보하지 못함.' if ko else 'A conditional review, not a trade instruction. No executable quote or exhaustive X timeline was obtained.'}</p></section></div><footer><span>OPSHNZ · official project sources · Federal Reserve · {stamp}</span><span>{'외노자 다니엘의 옵션 이야기' if ko else 'Options, every week — defidaniel'}</span></footer></div>'''
 (ROOT/f'scripts/current-{lang}.html').write_text(htmlDoc)
# Preserve all former material, then update the active editor and archive dated sections.
soup=BeautifulSoup((ROOT/'studio.html').read_text(),'html.parser');data=json.loads(soup.select_one('#weekly-data').string)
if not (ROOT/'studio-W42.html').exists():(ROOT/'studio-W42.html').write_text(str(soup))
data.update(week=week,snapshotAt=snap['at'],snapshotLabel=sourceTime,telegram=text,tweets=tweets,revision=cid,telegramCaption=f'{week} · 주간 온체인 옵션 검토본\n지표 {sourceTime} · 공식 발표 날짜 개별 표시',telegramParts=[text[text.index('【'+str(i)+'부】'):text.index('【'+str(i+1)+'부】') if i<3 else None].strip() for i in [1,2,3]])
koPath=f'{base}/onepager-ko.png';enPath=f'{base}/onepager-en.png';data['images']={'telegram':{'key':cid,'title':week+' 한국어 원페이저','path':koPath},'tweets':[{'key':f'{cid}-x-{i}','title':week+' English','path':enPath} for i in range(len(tweets))],'variants':{'ko':koPath,'en':enPath}}
soup.select_one('#weekly-data').string=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
head=soup.select_one('.page-heading');head.select_one('.eyebrow').string=f'OPTIONS WEEKLY · {week} · 3 PARTS'
for s in head.select('.week-label'):s.clear();s.append(sourceTime)
for sid in ['weeklyOnchain','tradingView','macroView','latestSource','projectNewsSources','individualCards','currentSources']:
 target=soup.find(id=sid)
 if target:
  target.decompose()
# Old source disclosures remain archived, not presented as current data.
for el in soup.select('main > details.source-details'):el.decompose()
nav=soup.select_one('.content-nav');nav.clear()
for href,label in [('index.html','← 업로드 달력'),('#onepager','한영 원페이저'),('#text','모바일 원고'),('studio-W42.html','W42 아카이브 ↗')]:
 a=soup.new_tag('a',href=href);a.string=label;nav.append(a)
pager=soup.select_one('#onepager');img=pager.select_one('img.onepager');img['src']=koPath;img.parent['href']=koPath;pager.select_one('.deliverable-heading .download')['href']=koPath
links=pager.select('.poster-lang-downloads a')
for a,src in zip(links,[koPath,enPath]):a['href']=src
for script in soup.find_all('script'):
 if script.get('id'):continue
 if 'const variants={ko:' in script.text:
  script.string=re.sub(r"const variants=\{ko:'[^']+',en:'[^']+'\}",f"const variants={{ko:'{koPath}',en:'{enPath}'}}",script.text)
soup.select_one('.source-freshness').string=f'{week} 검토본 · 지표 {sourceTime} · 신규 발표는 각 발표일 표시. 옵션 예시는 실제 호가가 아닙니다. 지난 영상은 역사 회차입니다.'
sources=soup.new_tag('details',attrs={'class':'grok-collector','id':'currentSources'});summary=soup.new_tag('summary');summary.string=f'{week} 출처와 확인 한계';sources.append(summary)
for url,label in [('https://opshnz.com/','OPSHNZ snapshot '+sourceTime),*[(n['url'],n['project']+' '+n['date']) for n in news],*[(e['url'],e['en']) for e in events]]:
 p=soup.new_tag('p');a=soup.new_tag('a',href=url,target='_blank',rel='noopener');a.string=label;p.append(a);sources.append(p)
for missing,tag,label in [('snapshotDate','p',sourceTime),('scopeInfo','p',week+' · 새 회차 검토본'),('downloadCopy','button','현재 원고 저장 ↓')]:
 if not soup.find(id=missing):
  el=soup.new_tag(tag,id=missing);el.string=label;sources.append(el)
p=soup.new_tag('p');p.string='자료 한계: 미집계 거래량은 0이 아님. 현물 API 범위는 제한됨. 완전한 X 타임라인·실제 체결 호가 미확보. 설명용 옵션 손익과 실제 시장 수치를 구분.';sources.append(p);soup.find('main').append(sources)
soup.select_one('#telegramPanel h2').string='이번 회차 · 모바일 한국어 원고'
(ROOT/'studio.html').write_text(str(soup))
# Render manifest is converted to a ready record only after assets are successfully rendered.
delivery=day+timedelta(days=1) if day.weekday()==6 else day
config={'id':cid,'approved':False,'validUntil':datetime.combine(delivery,datetime.max.time(),tzinfo=SGT).isoformat(),'text':f'{base}/telegram.txt','photo':koPath,'caption':data['telegramCaption']}
write('publish/telegram.json',config)
manifest={'preparedAt':now.isoformat(),'sourceWindowStart':str(day-timedelta(days=7)),'sourceWindowEnd':str(day-timedelta(days=1)),'snapshotAt':snap['at'],'deliveryDate':str(delivery),'configId':cid,'text':config['text'],'photo':koPath,'englishPhoto':enPath,'englishText':f'{base}/x.txt','sources':str(folder.relative_to(ROOT)),'limitations':limits+['No executable quotes; payoff is an illustrative 100/95 debit-2 example.','No exhaustive X timeline collection.','No new video produced.'],'news':news,'macro':events}
write('publish/weekly-build.json',manifest)
print(json.dumps({'id':cid,'sourceAt':sourceTime,'news':len(news),'draftChars':len(text),'tweets':len(tweets),'limits':limits},ensure_ascii=False))
