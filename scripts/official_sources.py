"""Discover dated public official updates. No AI inference, credentials or publishing."""
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import re
from bs4 import BeautifulSoup
FEEDS=[('Derive','https://insights.derive.xyz/rss/'),('Derive','https://blog.celestia.org/rss/')]
MONTHS={n:i for i,n in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
def recent(d,today):return today-timedelta(days=7)<=d<=today

def parse_rss(raw,project,today,feed):
 root=ET.fromstring(raw);out=[]
 for x in root.findall('./channel/item'):
  title=(x.findtext('title') or '').strip();url=(x.findtext('link') or '').strip()
  try:date=parsedate_to_datetime(x.findtext('pubDate') or '').date()
  except (ValueError,TypeError):continue
  if not recent(date,today):continue
  if 'celestia.org' in feed and 'derive' not in title.lower():continue
  if urlparse(url).scheme!='https' or urlparse(url).hostname!=urlparse(feed).hostname:continue
  out.append({'project':project,'date':date.isoformat(),'url':url,'title':title,'source':feed})
 return out

def parse_hypercall(raw,today):
 soup=BeautifulSoup(raw,'html.parser');out=[]
 for a in soup.select('a[href]'):
  text=a.get_text(' ',strip=True);m=re.match(r'([A-Z]{3}\s+\d{1,2},\s+\d{4})\s+(.+)',text)
  if not m:continue
  try:date=datetime.strptime(m[1],'%b %d, %Y').date()
  except ValueError:continue
  if not recent(date,today):continue
  title=(a.find(['h2','h3']) or a).get_text(' ',strip=True)
  title=re.sub(r'^[A-Z]{3}\s+\d{1,2},\s+\d{4}\s*','',title)
  url=urljoin('https://blog.hypercall.xyz/',a['href'])
  if urlparse(url).hostname!='blog.hypercall.xyz':continue
  out.append({'project':'Hypercall','date':date.isoformat(),'url':url,'title':title,'source':'https://blog.hypercall.xyz/'})
 return out

def parse_aevo(raw,today):
 soup=BeautifulSoup(raw,'html.parser');out=[]
 for msg in soup.select('.tgme_widget_message'):
  dateNode=msg.select_one('time[datetime]');body=msg.select_one('.tgme_widget_message_text');link=msg.select_one('.tgme_widget_message_date[href]')
  if not dateNode or not body or not link:continue
  try:date=datetime.fromisoformat(dateNode['datetime'].replace('Z','+00:00')).date()
  except ValueError:continue
  if not recent(date,today):continue
  text=body.get_text(' ',strip=True)
  if not re.search(r'option|aevo|buyback|burn',text,re.I):continue
  url=link['href']
  if not url.startswith('https://t.me/aevoupdates/'):continue
  out.append({'project':'Aevo','date':date.isoformat(),'url':url,'title':text[:160],'source':'https://t.me/s/aevoupdates'})
 return out

def parse_fomc(raw,today):
 soup=BeautifulSoup(raw,'html.parser');out=[]
 for year in [today.year,today.year+1]:
  header=soup.find(string=lambda s:s and f'{year} FOMC Meetings' in s)
  if not header:continue
  panel=header.find_parent(class_='panel')
  if not panel:continue
  for row in panel.select('.fomc-meeting'):
   month=row.select_one('.fomc-meeting__month');dates=row.select_one('.fomc-meeting__date')
   if not month or not dates:continue
   m=MONTHS.get(month.get_text(' ',strip=True));d=re.fullmatch(r'\s*(\d{1,2})\s*[-–]\s*(\d{1,2})\s*\*?\s*',dates.get_text(' ',strip=True))
   if not m or not d:continue
   try:start=datetime(year,m,int(d[1])).date();end=datetime(year,m,int(d[2])).date()
   except ValueError:continue
   if end+timedelta(days=1)<today or start>today+timedelta(days=7):continue
   out.append({'date':start.isoformat(),'endDate':end.isoformat(),'ko':f'FOMC 회의 · 미국 현지 날짜 {m}/{start.day}–{end.day}','en':f'FOMC meeting · {start.isoformat()} to {end.isoformat()}, US dates','url':'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm','verify':d[0].replace('*','').strip()})
 return out

def describe(item):
 title=' '.join(item['title'].split()[:10]);item={**item,'originalTitle':title}
 lower=title.lower()
 if 'coming' in lower and 'covered call' in lower:
  ko='커버드콜 기능을 예고한 공식 글입니다. 출시 완료와 구분해 봅니다.'
 elif 'v3' in lower and item['project']=='Derive':
  ko='Derive V3 관련 기술 글을 공개했습니다. 구현과 운영 구조를 다룬 글로, 신규 토큰 상장 공지는 아닙니다.'
 elif 'buyback' in lower or 'burn' in lower:
  ko='바이백·소각 관련 공식 공지를 확인했습니다. 수치·적용 조건은 아래 원문을 기준으로 확인합니다.'
 else:ko='옵션 프로젝트의 새 공식 글을 확인했습니다. 발표 범위와 적용 조건은 원문에서 확인합니다.'
 item['ko']=ko+'\n공식 제목: '+title
 item['en']='Official update: '+title+'. Publication verified; read the source for product status and terms.'
 item['verify']=title[:45]
 return item

def discover(fetch,today,folder):
 news=[];errors=[]
 for project,url in FEEDS:
  try:
   raw=fetch(url);(folder/('feed-'+('celestia' if 'celestia' in url else 'derive')+'.xml')).write_text(raw)
   news.extend(parse_rss(raw,project,today,url))
  except Exception as e:errors.append(f'{url}: {type(e).__name__}')
 for url,parser,name in [('https://blog.hypercall.xyz/',parse_hypercall,'hypercall-index'),('https://t.me/s/aevoupdates',parse_aevo,'aevo-channel')]:
  try:
   raw=fetch(url);(folder/(name+'.html')).write_text(raw);news.extend(parser(raw,today))
  except Exception as e:errors.append(f'{url}: {type(e).__name__}')
 # Prefer a project's own dated feed over partner commentary, and one item per project.
 news.sort(key=lambda n:(n['date'],'celestia.org' not in n['source']),reverse=True)
 unique={}
 for n in news:
  if n['project'] not in unique:unique[n['project']]=describe(n)
 events=[]
 try:
  raw=fetch('https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm');(folder/'fed-calendar.html').write_text(raw);events=parse_fomc(raw,today)
 except Exception as e:errors.append('Fed calendar: '+type(e).__name__)
 return list(unique.values()),events,errors
