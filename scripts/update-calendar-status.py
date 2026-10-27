from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,re,sys
root=Path(__file__).resolve().parents[1];mode=sys.argv[1];now=datetime.now(ZoneInfo('Asia/Singapore'));date=now.date().isoformat();p=root/'index.html';s=p.read_text();m=re.search(r'(<script id="calendar-seed" type="application/json">)(.*?)(</script>)',s,re.S);rows=json.loads(m[2]);ready=json.loads((root/'publish/weekly-ready.json').read_text());id=('weekly-prepare-' if mode=='prepared' else 'weekly-draft-')+date
item=next((e for e in rows if e['id']==id),None)
if item is None:
 item={'id':id,'title':'주간 옵션 검토본 · 복구 준비' if mode=='prepared' else '주간 옵션 검토본 · 개인 봇 전달','date':date,'time':now.strftime('%H:%M'),'channel':'봇 미리보기','formats':['원페이저','글'],'status':'검토대기','link':'','note':''};rows.append(item)
item.update(status='검토대기' if mode=='prepared' else '게시완료',note=f"{ready['configId']} · "+('새 자료·한영 원페이저·모바일 원고 검증 완료. 개인 봇 전달 대기.' if mode=='prepared' else '개인 봇 전송 성공과 receipt 확인 완료. 공지방 게시 없음.'),link='studio.html' if False else ('https://optioncontent.vercel.app/studio.html' if mode=='prepared' else 'https://t.me/wenojadaniel_options_bot'),updatedAt=now.isoformat())
s=s[:m.start(2)]+json.dumps(rows,ensure_ascii=False)+s[m.end(2):];p.write_text(s)
