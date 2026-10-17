#!/usr/bin/env python3
"""Check the built pages, links, language alternates, galleries, image provenance and public hygiene.

  python3 scripts/validate.py                     missing poster sets are listed, not errors
  python3 scripts/validate.py --require-complete  every device × language poster set must exist
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote, parse_qs
import argparse
import hashlib
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build  # noqa: E402  (site definition: languages, device groups, copy)

parser_args = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser_args.add_argument('--require-complete', action='store_true', help='treat a missing device × language poster set as an error')
ARGS = parser_args.parse_args()
build.load()

CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'"
TOUCH_ICON = 'assets/images/apple-touch-icon.png'
COMPETITORS = ['Evernote', 'Obsidian', 'Notion', 'Bear', 'Day One', 'Drafts', 'Ulysses', 'Typora', 'OneNote', 'Joplin', 'Logseq', 'Apple Notes']
PRIVATE_MARKERS = ['SUPPORT_EMAIL', 'OPERATOR_NAME', 'PRIVACY_EFFECTIVE_DATE', '/Users/phil', '/tmp/zebra', 'sourceSidecar', 'createdRecord', 'javascript:']
errors = []


class Page(HTMLParser):
 def __init__(self, path, locale):
  super().__init__()
  self.path = path; self.locale = locale; self.ids = set(); self.refs = []; self.gallery = ''; self.in_data = False
  self.h1s = 0; self.images = 0; self.faqs = 0; self.videos = 0; self.alternates = {}; self.canonical = None; self.touch_icon = None
  self.language_links = []; self.device_buttons = []; self.html_lang = None; self.csp = None; self.fallback = None
  self.texts = []; self.skip_text = 0; self.external = []; self.og_image = None

 def handle_starttag(self, tag, attrs):
  a = dict(attrs)
  if 'id' in a:
   if a['id'] in self.ids: errors.append(f'{self.path}: duplicate id {a["id"]}')
   self.ids.add(a['id'])
  if tag == 'html': self.html_lang = a.get('lang')
  if tag == 'h1': self.h1s += 1
  if tag == 'details' and a.get('id', '').startswith('faq-'): self.faqs += 1
  if tag == 'img':
   self.images += 1
   if 'alt' not in a: errors.append(f'{self.path}: image without alt')
  if tag == 'meta' and a.get('http-equiv') == 'Content-Security-Policy': self.csp = a.get('content')
  if tag == 'meta' and a.get('property') == 'og:image': self.og_image = a.get('content', '')
  if tag == 'link':
   rel = a.get('rel', '')
   if rel == 'alternate' and 'hreflang' in a: self.alternates[a['hreflang']] = a['href']
   elif rel == 'canonical': self.canonical = a['href']
   else:
    self.refs.append(a.get('href', ''))
    if rel == 'apple-touch-icon': self.touch_icon = a.get('href')
    if rel in ('stylesheet', 'icon', 'apple-touch-icon', 'preload') and urlsplit(a.get('href', '')).netloc: self.external.append(a['href'])
  if tag == 'a':
   self.refs.append(a.get('href', ''))
   if 'hreflang' in a: self.language_links.append(a)
  if tag in ['img', 'script', 'source']:
   self.refs.append(a.get('src', ''))
   if urlsplit(a.get('src', '')).netloc: self.external.append(a['src'])
  if tag == 'video':
   self.videos += 1; self.refs.append(a.get('poster', ''))
   if 'autoplay' in a: errors.append(f'{self.path}: the film must not autoplay before reduced-motion is checked')
   if 'muted' not in a or 'playsinline' not in a: errors.append(f'{self.path}: the film must be muted and inline')
  if 'data-large' in a: self.refs.append(a['data-large'])
  if 'data-device-button' in a: self.device_buttons.append(a['data-device-button'])
  if 'srcset' in a: self.refs.extend(x.strip().split()[0] for x in a['srcset'].split(','))
  if a.get('id') == 'gallery-fallback': self.fallback = 'hidden' not in a
  if tag in ('script', 'style'): self.skip_text += 1
  self.in_data = tag == 'script' and a.get('id') == 'gallery-data'

 def handle_endtag(self, tag):
  if tag == 'script': self.in_data = False
  if tag in ('script', 'style'): self.skip_text -= 1

 def handle_data(self, data):
  if self.in_data: self.gallery += data
  elif not self.skip_text and data.strip(): self.texts.append(data)


def resolve(page_path, ref):
 u = urlsplit(ref)
 target = (page_path.parent / unquote(u.path)).resolve() if u.path else page_path
 return target / 'index.html' if target.is_dir() else target


# Pages ----------------------------------------------------------------------------------------
pages = {}
for locale, meta in build.LOCALES.items():
 for filename in build.PAGES:
  name = meta['dir'] + filename; p = ROOT / name
  if not p.is_file(): errors.append(f'{name}: page missing; run scripts/build.py'); continue
  parser = Page(name, locale); text = p.read_text(); parser.feed(text); pages[p.resolve()] = parser
  parser.filename = filename
  if parser.h1s != 1: errors.append(f'{name}: expected one h1')
  if parser.html_lang != meta['lang']: errors.append(f'{name}: html lang {parser.html_lang!r}, expected {meta["lang"]!r}')
  if parser.csp != CSP: errors.append(f'{name}: Content-Security-Policy changed or missing')
  if parser.external: errors.append(f'{name}: external resources {parser.external}')
  for bad in PRIVATE_MARKERS:
   if bad in text: errors.append(f'{name}: private or placeholder marker {bad}')

  # Reciprocal hreflang alternates for every language plus x-default; canonical is self.
  expected = {o['lang']: f"{build.BASE}{o['dir']}{filename}" for o in build.LOCALES.values()}
  expected['x-default'] = f"{build.BASE}{build.LOCALES[build.FALLBACK_LOCALE]['dir']}{filename}"
  if parser.alternates != expected: errors.append(f'{name}: hreflang alternates {parser.alternates} differ from {expected}')
  if parser.canonical != f"{build.BASE}{name}": errors.append(f'{name}: canonical {parser.canonical}')
  og = urlsplit(parser.og_image or '')
  if not (parser.og_image or '').startswith(build.BASE) or not (ROOT / og.path[len(urlsplit(build.BASE).path):]).is_file():
   errors.append(f'{name}: og:image {parser.og_image} is not a published site image')

  # Language switcher: the other three languages, by their own names, to the same page.
  links = {a['hreflang']: a for a in parser.language_links}
  others = {k: o for k, o in build.LOCALES.items() if k != locale}
  if set(links) != {o['lang'] for o in others.values()} or len(parser.language_links) != len(others):
   errors.append(f'{name}: language links {sorted(links)} should be {sorted(o["lang"] for o in others.values())}')
  for key, other in others.items():
   a = links.get(other['lang'])
   if not a: continue
   if a.get('lang') != other['lang']: errors.append(f'{name}: language link to {other["name"]} lacks lang="{other["lang"]}"')
   if resolve(p, a['href']) != (ROOT / other['dir'] / filename).resolve(): errors.append(f'{name}: language link {a["href"]} is not the {key} {filename}')
  if 'class="language-menu"' not in text or '<summary>' not in text.split('class="language-menu"', 1)[1][:600]:
   errors.append(f'{name}: language switcher must be a native <details> disclosure')
  if parser.touch_icon is None or resolve(p, parser.touch_icon) != (ROOT / TOUCH_ICON).resolve():
   errors.append(f'{name}: missing apple-touch-icon link to {TOUCH_ICON}')

  # Copy hygiene: no competitor names; French spacing; the Japanese word for a note is ノート.
  body = ' '.join(parser.texts)
  for name_ in COMPETITORS:
   if re.search(rf'\b{re.escape(name_)}\b', body): errors.append(f'{name}: mentions {name_}')
  if locale == 'fr-FR':
   # : ; ! ? » take a no-break space before them, « one after it; an ordinary space or none is wrong.
   for t in parser.texts:
    for m in re.finditer(r'(?<=[ \w])[:;!?»]|«(?=[ \w])', t):
     errors.append(f'{name}: French punctuation needs a no-break space: …{t[max(0, m.start() - 15):m.end() + 15]}…')
   if "'" in body: errors.append(f"{name}: straight apostrophe in French text")
  if locale == 'ja' and re.search(r'メモ(?!リ)', body): errors.append(f'{name}: Japanese copy should call a note ノート, not メモ')

  if filename != 'index.html': continue
  if parser.faqs != 8: errors.append(f'{name}: expected 8 FAQs, found {parser.faqs}')
  if parser.videos != 1: errors.append(f'{name}: expected one promo film')
  data = json.loads(parser.gallery)
  shown = [d['id'] for d in build.DEVICES if build.image_locale(d['id'], locale)]
  if list(data['devices']) != shown: errors.append(f'{name}: gallery devices {list(data["devices"])}, expected {shown}')
  if parser.device_buttons != list(data['devices']): errors.append(f'{name}: device buttons {parser.device_buttons} do not match gallery data')
  for device, cards in data['devices'].items():
   source = data['imageLocales'].get(device)
   if source not in (locale, build.FALLBACK_LOCALE): errors.append(f'{name}: {device} uses {source} images')
   if source != locale and parser.fallback is None: errors.append(f'{name}: {device} shows {source} images without the fallback note')
   if len(cards) != len(build.SCENES): errors.append(f'{name}: {device} expected {len(build.SCENES)} cards')
   copy = next(d['copy'] for d in build.DEVICES if d['id'] == device)
   if [c['headline'] for c in cards] != [c['headline'] for c in build.FEATURES[copy][locale]]: errors.append(f'{name}: {device} captions are not the {locale} {copy} copy')
   for card in cards:
    for kind in ['small', 'large']:
     if f'/{device}/{source}/' not in card[kind]: errors.append(f'{name}: {card[kind]} is not a {device}/{source} image')
     if not resolve(p, card[kind]).is_file(): errors.append(f'{name}: missing {card[kind]}')
     parser.refs.append(card[kind])
  if parser.fallback is not None and parser.fallback != (data['imageLocales']['macos'] != locale):
   errors.append(f'{name}: fallback note visibility does not match the Mac gallery')

for p, parser in pages.items():
 for ref in parser.refs:
  if not ref: continue
  u = urlsplit(ref)
  if u.scheme or u.netloc: continue
  target = resolve(p, ref)
  if not target.is_relative_to(ROOT): errors.append(f'{parser.path}: link leaves site {ref}')
  elif not target.exists(): errors.append(f'{parser.path}: missing link {ref}')
  elif u.fragment and target in pages and u.fragment not in pages[target].ids: errors.append(f'{parser.path}: missing anchor {ref}')
 # Reciprocity: every alternate page lists this page back.
 for href in parser.alternates.values():
  other = pages.get((ROOT / href[len(build.BASE):]).resolve())
  if other is None: errors.append(f'{parser.path}: alternate {href} is not a built page')
  elif parser.canonical not in other.alternates.values(): errors.append(f'{other.path}: does not list {parser.canonical} back')

# Scripts and content ----------------------------------------------------------------------------
js = (ROOT / 'assets/site.js').read_text()
if re.search(r'\b(fetch|XMLHttpRequest|WebSocket|eval)\s*\(', js): errors.append('Unexpected network or eval API in site.js')
if re.search(r'@import|url\(\s*["\']?(https?:)?//', (ROOT / 'assets/site.css').read_text()): errors.append('site.css loads a remote resource')
for p in list((ROOT / 'content').glob('*.json')) + list((ROOT / 'assets').glob('*.js')):
 text = p.read_text()
 for marker in ['/Users/phil/', '/tmp/zebra-store', 'OPERATOR_NAME', 'SUPPORT_EMAIL', 'createdRecord']:
  if marker in text: errors.append(f'{p.relative_to(ROOT)}: private/placeholder marker {marker}')


def png_info(path):
 """(width, height, colour type, has tRNS) from a PNG header."""
 data = path.read_bytes()
 if data[:8] != b'\x89PNG\r\n\x1a\n': return None
 width, height, _, colour = struct.unpack('>IIBB', data[16:26])
 return width, height, colour, b'tRNS' in data


def check_file(item, label):
 p = (ROOT / item['path']).resolve()
 if not p.is_file(): errors.append(f'Missing {label}: {item["path"]}'); return None
 data = p.read_bytes()
 if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']: errors.append(f'{label} hash or size mismatch: {item["path"]}')
 return p


# Image and video provenance -------------------------------------------------------------------
coverage, missing_sets = {}, []
manifest = ROOT / 'asset-manifest.json'
try:
 metadata = json.loads(manifest.read_text()); posters = metadata['posters']; seen = set(); identities = set()
 devices = {d['id'] for d in build.DEVICES}
 for poster in posters:
  identity = (poster['platform'], poster['locale'], poster['scene'])
  if identity in identities: errors.append(f'Duplicate poster identity: {identity}')
  identities.add(identity)
  if poster['platform'] not in devices or poster['locale'] not in build.LOCALES or poster['scene'] not in build.SCENES:
   errors.append(f'Poster outside the site definition: {identity}')
  elif poster['slug'] != f"{build.SCENES.index(poster['scene']) + 1:02}-{poster['scene']}": errors.append(f'Unexpected slug {poster["slug"]} for {identity}')
  if not any(a.get('id') == 'zebra-window-mascot' for a in poster.get('decorativeAssets', [])): errors.append(f'Missing mascot provenance: {identity}')
  if set(poster['variants']) != {'small', 'large'}: errors.append(f'Wrong variants for {identity}')
 branding = {item['id']: item for item in metadata['branding']}
 for required in ('icon', 'mascot', 'apple-touch-icon'):
  if required not in branding: errors.append(f'Image manifest lacks the {required} branding entry')
 assets = [a for poster in posters for a in poster['variants'].values()] + metadata['branding']
 versions = {(ROOT / a['path']).resolve(): a['sha256'][:12] for poster in posters for a in poster['variants'].values()}
 versions.update({(ROOT / item['path']).resolve(): item['sha256'][:12] for video in metadata.get('videos', []) for item in (video, video['poster'])})
 for page_path, parser in pages.items():
  for ref in parser.refs:
   u = urlsplit(ref)
   if u.scheme or u.netloc: continue
   target = resolve(page_path, ref)
   if target in versions and parse_qs(u.query).get('v') != [versions[target]]: errors.append(f'{parser.path}: missing or stale image version {ref}')
 for asset in assets:
  p = (ROOT / asset['path']).resolve()
  if not p.is_relative_to(ROOT / 'assets/images'): errors.append(f'Image path leaves assets: {asset["path"]}'); continue
  if p in seen: errors.append(f'Duplicate image path: {asset["path"]}')
  seen.add(p); check_file(asset, 'manifest image')
 actual = {p.resolve() for p in (ROOT / 'assets/images').rglob('*') if p.is_file() and p.name != '.DS_Store'}
 if seen != actual:
  extra = sorted(str(p.relative_to(ROOT)) for p in actual - seen); absent = sorted(str(p.relative_to(ROOT)) for p in seen - actual)
  errors.append(f'Image manifest does not exactly cover the image files (unlisted: {extra[:5]}{"…" if len(extra) > 5 else ""}; absent: {absent[:5]})')
 info = png_info(ROOT / TOUCH_ICON) if (ROOT / TOUCH_ICON).is_file() else None
 if info is None: errors.append(f'{TOUCH_ICON} is missing or not a PNG')
 elif info[:2] != (180, 180) or info[2] not in (0, 2) or info[3]: errors.append(f'{TOUCH_ICON} must be an opaque 180×180 PNG without alpha, got {info}')
 videos = metadata.get('videos', []); covered = set()
 if build.FALLBACK_LOCALE not in {v['locale'] for v in videos}: errors.append(f'Video manifest needs the {build.FALLBACK_LOCALE} film, used as the fallback')
 for video in videos:
  if video['locale'] not in build.LOCALES: errors.append(f'Video for an unknown language: {video["locale"]}')
  for item in (video, video['poster']):
   covered.add((ROOT / item['path']).resolve()); check_file(item, 'manifest video file')
 if covered != {p.resolve() for p in (ROOT / 'assets/video').rglob('*') if p.is_file() and p.name != '.DS_Store'}: errors.append('Video manifest does not exactly cover all video files')
 # Which device × language poster sets exist, and what the pages show instead.
 present = {}
 for poster in posters:
  if all((ROOT / v['path']).is_file() for v in poster['variants'].values()):
   present.setdefault((poster['platform'], poster['locale']), set()).add(poster['scene'])
 for device in build.DEVICES:
  coverage[device['label']] = {}
  for locale in build.LOCALES:
   have = present.get((device['id'], locale), set()); coverage[device['label']][locale] = f'{len(have)}/{len(build.SCENES)}'
   if len(have) == len(build.SCENES): continue
   source = build.image_locale(device['id'], locale)
   effect = 'tab hidden' if source is None else f'shows {source} images with a note'
   missing = [s for s in build.SCENES if s not in have]
   missing_sets.append(f"{device['label']} · {locale}: {len(missing)} of {len(build.SCENES)} scenes missing → {effect}")
   if ARGS.require_complete: errors.append(f"Incomplete poster set: {device['label']} · {locale} lacks {', '.join(missing)}")
except (ValueError, KeyError, TypeError) as exc:
 errors.append(f'Invalid image manifest: {exc}')

webp = list((ROOT / 'assets/images').rglob('*.webp'))
cards = sum(len(c) for parser in pages.values() if parser.gallery for c in json.loads(parser.gallery)['devices'].values())
result = {'pages': len(pages), 'languages': list(build.LOCALES), 'galleryCards': cards, 'webImages': len(webp),
          'films': sum(p.videos for p in pages.values()), 'localLinksChecked': sum(len(p.refs) for p in pages.values()),
          'posterCoverage': coverage, 'missingPosterSets': missing_sets, 'errors': errors}
print(json.dumps(result, indent=2, ensure_ascii=False))
sys.exit(bool(errors))
