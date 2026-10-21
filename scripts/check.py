"""Offline content/asset integrity check. Python 3 standard library only."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import json, re, zipfile
root = Path(__file__).resolve().parents[1]
errors = []
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('src', 'href', 'poster') and value:
                self.links.append(value)
for relative in ['index.html', 'studio.html', 'assets/bear-put-spread-payoff.html', 'scripts/weekly-ko-W42.html', 'scripts/weekly-en-W42.html']:
    file = root / relative
    text = file.read_text()
    parser = Links(); parser.feed(text)
    links = parser.links + re.findall(r'url\([\'"]?([^\)\'"\s]+)', text)
    for url in links:
        if urlsplit(url).scheme or url.startswith(('#', '//')) or '${' in url:
            continue
        target = file.parent / unquote(urlsplit(url).path)
        if not target.exists(): errors.append(f'{relative}: missing {url}')
text = (root/'studio.html').read_text()
match = re.search(r'<script[^>]*id="weekly-data"[^>]*>(.*?)</script>', text, re.S)
data = json.loads(match[1])
assert len(data['tweets']) == 17
assert len(data['telegram']) <= 4096
for media in [data['images']['telegram'], *data['images']['tweets']]:
    if not (root / media['path']).is_file(): errors.append('Missing media: '+media['path'])
for file in root.rglob('*.json'):
    if '.git' not in file.parts and 'node_modules' not in file.parts: json.loads(file.read_text())
for file in (root/'assets').glob('*.zip'):
    with zipfile.ZipFile(file) as archive:
        if archive.testzip(): errors.append('Corrupt ZIP: '+file.name)
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: local links, JSON, ZIP integrity, {len(data["tweets"])} X posts, {len(data["telegram"])} Telegram characters.')
