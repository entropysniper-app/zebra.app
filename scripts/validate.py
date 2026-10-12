#!/usr/bin/env python3
"""Check local pages, links, bilingual galleries, image hashes and public hygiene."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]
class Page(HTMLParser):
 def __init__(self, path):
  super().__init__(); self.path=path; self.ids=set(); self.refs=[]; self.gallery=''; self.in_data=False; self.h1s=0; self.images=0; self.faqs=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:
   if a['id'] in self.ids: errors.append(f'{self.path}: duplicate id {a["id"]}')
   self.ids.add(a['id'])
  if tag=='h1':self.h1s+=1
  if tag=='details':self.faqs+=1
  if tag=='img':
   self.images+=1
   if 'alt' not in a:errors.append(f'{self.path}: image without alt')
  if tag in ['a','link']:self.refs.append(a.get('href',''))
  if tag in ['img','script']:self.refs.append(a.get('src',''))
  if 'srcset' in a:self.refs.extend(x.strip().split()[0] for x in a['srcset'].split(','))
  self.in_data=tag=='script' and a.get('id')=='gallery-data'
 def handle_endtag(self,tag):
  if tag=='script':self.in_data=False
 def handle_data(self,data):
  if self.in_data:self.gallery+=data

pages={}
for name in ['index.html','privacy.html','zh/index.html','zh/privacy.html']:
 p=ROOT/name;parser=Page(name);parser.feed(p.read_text());pages[p.resolve()]=parser
 if parser.h1s!=1:errors.append(f'{name}: expected one h1')
 if name.endswith('index.html'):
  if parser.faqs!=8:errors.append(f'{name}: expected 8 FAQs')
  data=json.loads(parser.gallery)
  for platform,cards in data['devices'].items():
   if len(cards)!=10:errors.append(f'{name}: {platform} expected 10 cards')
   for card in cards:
    for kind in ['small','large']:
     if not (p.parent/card[kind]).is_file():errors.append(f'{name}: missing {card[kind]}')
 for bad in ['SUPPORT_EMAIL','OPERATOR_NAME','PRIVACY_EFFECTIVE_DATE','/Users/phil','/tmp/zebra','sourceSidecar','createdRecord','javascript:']:
  if bad in p.read_text():errors.append(f'{name}: private or placeholder marker {bad}')
for p,parser in pages.items():
 for ref in parser.refs:
  if not ref:continue
  u=urlsplit(ref)
  if u.scheme or u.netloc:continue
  target=(p.parent/unquote(u.path)).resolve() if u.path else p
  if target.is_dir():target=target/'index.html'
  if not target.is_relative_to(ROOT):errors.append(f'{parser.path}: link leaves site {ref}')
  elif not target.exists():errors.append(f'{parser.path}: missing link {ref}')
  elif u.fragment and target in pages and u.fragment not in pages[target].ids:errors.append(f'{parser.path}: missing anchor {ref}')

# Every browser script and stylesheet is local; no runtime third-party requests.
js=(ROOT/'assets/site.js').read_text()
if re.search(r'\b(fetch|XMLHttpRequest|WebSocket|eval)\s*\(',js):errors.append('Unexpected network or eval API in site.js')
for p in list((ROOT/'content').glob('*.json'))+list((ROOT/'assets').glob('*.js')):
 text=p.read_text()
 for marker in ['/Users/phil/','/tmp/zebra-store','OPERATOR_NAME','SUPPORT_EMAIL','createdRecord']:
  if marker in text:errors.append(f'{p.relative_to(ROOT)}: private/placeholder marker {marker}')
images=list((ROOT/'assets/images').rglob('*.webp'))
if len(images)!=120:errors.append(f'Expected 120 WebP derivatives, found {len(images)}')
manifest=ROOT/'asset-manifest.json'
if not manifest.exists():errors.append('Missing image provenance manifest')
else:
 try:
  metadata=json.loads(manifest.read_text()); posters=metadata['posters']; seen=set(); identities=set()
  if len(posters)!=60:errors.append('Image manifest must describe 60 source posters')
  for poster in posters:
   identity=(poster['platform'],poster['locale'],poster['scene'])
   if identity in identities:errors.append(f'Duplicate poster identity: {identity}')
   identities.add(identity)
   if not any(a.get('id')=='zebra-window-mascot' for a in poster['decorativeAssets']):errors.append(f'Missing mascot provenance: {identity}')
   if set(poster['variants'])!={'small','large'}:errors.append(f'Wrong variants for {identity}')
  assets=[a for poster in posters for a in poster['variants'].values()]+metadata['branding']
  for asset in assets:
   p=(ROOT/asset['path']).resolve()
   if not p.is_relative_to(ROOT/'assets/images'):errors.append(f'Image path leaves assets: {asset["path"]}');continue
   if p in seen:errors.append(f'Duplicate image path: {asset["path"]}')
   seen.add(p)
   if not p.is_file():errors.append(f'Missing manifest image: {asset["path"]}');continue
   data=p.read_bytes()
   if len(data)!=asset['bytes'] or hashlib.sha256(data).hexdigest()!=asset['sha256']:errors.append(f'Image hash or size mismatch: {asset["path"]}')
  actual={p.resolve() for p in (ROOT/'assets/images').rglob('*') if p.is_file()}
  if seen!=actual:errors.append('Image manifest does not exactly cover all image files')
 except (ValueError,KeyError,TypeError) as exc:errors.append(f'Invalid image manifest: {exc}')
result={'pages':len(pages),'localizedFeatureCards':60,'webImages':len(images),'localLinksChecked':sum(len(p.refs) for p in pages.values()),'errors':errors}
print(json.dumps(result,indent=2))
sys.exit(bool(errors))
