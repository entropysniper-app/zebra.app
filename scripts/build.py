#!/usr/bin/env python3
"""Generate a buildless, bilingual GitHub Pages site from reviewed copy."""
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://entropysniper-app.github.io/zebra.app/'
FEATURES = json.loads((ROOT / 'content/features.json').read_text())
SUPPORT = json.loads((ROOT / 'content/support.json').read_text())
MANIFEST = json.loads((ROOT / 'asset-manifest.json').read_text())
POSTER_ASSETS = {
 asset['path']: asset
 for poster in MANIFEST['posters']
 for asset in poster['variants'].values()
}
VIDEOS = {video['locale']: video for video in MANIFEST.get('videos', [])}
FILM = {
 'en-US': {'eyebrow':'Zebra in 14 seconds','title':'Watch an idea take shape.','caption':'Every app screen in this film is a real Zebra capture; the moving type is added for the film.','play':'Play video','pause':'Pause video','label':'Zebra promo film'},
 'zh-Hans': {'eyebrow':'14 秒认识 Zebra','title':'看一个想法慢慢成形。','caption':'片中 App 画面均为 Zebra 真实截图，动态文字为短片另加。','play':'播放视频','pause':'暂停视频','label':'Zebra 宣传短片'},
}
E = html.escape
UI = {
 'en-US': {
  'lang':'en','other':'简体中文','skip':'Skip to content','features':'Explore','sync':'Sync','support':'Support','privacy':'Privacy & data','home':'Home',
  'title':'Zebra — Markdown notes, diagrams, math & more','description':'A native Markdown notebook for Mac, iPhone and iPad. Write, organize, find and carry your ideas across your own devices. Explore Zebra and get support.',
  'eyebrow':'Markdown notes · Mac, iPhone & iPad','hero':'Type Markdown.\nGive ideas their full shape.','lead':'Type the syntax. See it formatted. Add diagrams, math, code, and editable tables as your ideas grow—from a quick note to a piece worth sharing.',
  'explore':'Meet Zebra','help':'Get help','caption':'Zebra on Mac · fictional notes, real app screenshots',
  'principles':['Native Markdown writing','Your notes, local by default','Optional iCloud sync'],
  'galleryEyebrow':'A little note. A bigger picture.','galleryTitle':'More ways to make yourself clear.','galleryIntro':'Start with a sentence. Add the details that make it yours. Choose a device to see what Zebra can do there.',
  'view':'View screenshot:','status':'10 features','galleryNote':'Real app screens with sample notes. The zebra is our illustrated window companion. The sync diagram explains the strategy; it is not a live sync recording.',
  'syncEyebrow':'Concurrent editing · Private iCloud sync','syncTitle':'Your edits merge\nautomatically.','syncIntro':'Add a task on iPhone while revising a plan on Mac. Concurrent edits to ordinary note text merge when you sync, reducing the work of choosing between conflict copies.',
  'syncMark':'Your devices · Same Apple Account · Your choice',
  'ordinaryTitle':'Ordinary notes: edits come together.','ordinaryBody':'Enable iCloud sync on devices signed in to the same Apple Account. Concurrent changes to note text merge automatically. Write offline and sync when you reconnect. Sync is off by default on new installations.',
  'encryptedTitle':'Encrypted notes: keep the versions.','encryptedBody':'Concurrent encrypted edits remain as separate versions. Unlock, review, and restore what you need; titles and some outer metadata remain visible.',
  'platformTitle':'At home on each device.','platformCaption':'The same writing essentials, with extra tools on Mac.','platformHeads':['Capability','Mac','iPhone & iPad'],
  'platformRows':[
   ['Write & organize','Markdown, tables, diagrams, math, code, folders and nested tags','Markdown, tables, diagrams, math, code, folders and nested tags'],
   ['Find','Local semantic + keyword search, find within notes','Keyword search and find within notes'],
   ['Bring in & take out','Local document conversion and exports including PDF, DOCX and ePub','Photo and file attachments; share Markdown or a note package'],
   ['Appearance','22 themes, custom colors, and theme-file import/export','22 themes, with typography and layout options'],
   ['Continue writing','Optional iCloud sync with your own devices','Optional iCloud sync with your own devices']],
  'supportEyebrow':'A helping hoof','supportTitle':'A few useful answers.','supportIntro':'From the first note to a detail worth finding again. Here is how writing, search, sync and your data work.',
  'contactTitle':'Something not quite right?','contactBody':'Email us for help or privacy questions. Include your device, Zebra version, what you expected and what happened. You can also report a public issue on GitHub.','contactAction':'Report a public issue ↗','emailAction':'Email support','emailFooter':'Email us','privacyContactTitle':'Support and privacy questions','privacyContactBody':'Contact us at the email address below for help with Zebra or questions about how your data is handled.',
  'footer':'Made for the way ideas happen.','source':'GitHub','close':'Close screenshot','noScript':'These Mac screenshots and the support content work without JavaScript. Enable JavaScript to switch devices and open larger images.',
  'privacyTitle':'Privacy & data — Zebra','privacyType':'Product data-handling information','back':'Back to Zebra','githubPrivacy':'GitHub Privacy Statement',
 },
 'zh-Hans': {
  'lang':'zh-Hans','other':'English','skip':'跳到正文','features':'功能','sync':'同步','support':'支持','privacy':'隐私与数据','home':'首页',
  'title':'Zebra — Markdown 笔记、图表、公式与代码','description':'为 Mac、iPhone 和 iPad 打造的原生 Markdown 笔记。写作、整理、找回线索，在自己的设备间接着写。了解 Zebra 的功能与使用帮助。',
  'eyebrow':'Markdown 笔记 · Mac、iPhone 与 iPad','hero':'直接写 Markdown，\n把想法写完整。','lead':'敲下语法，看到排版。标题、列表、代码块直接输入，图表、公式与可编辑表格接着补上。从随手记一句，到认真写一篇，都在 Zebra。',
  'explore':'认识 Zebra','help':'获取帮助','caption':'Mac 上的 Zebra · 虚构演示内容，真实 App 界面',
  'principles':['原生 Markdown 写作','笔记默认留在本机','按需开启 iCloud 同步'],
  'galleryEyebrow':'从一句话，到一套想法','galleryTitle':'让表达，多几种可能。','galleryIntro':'从文字开始，慢慢补全细节。选择你的设备，看看 Zebra 如何承载不同的想法。',
  'view':'查看截图：','status':'10 个使用场景','galleryNote':'画面来自真实 App，笔记为演示内容。趴窗斑马是独立插画；同步图用于解释机制，并非实时同步录像。',
  'syncEyebrow':'多端并发编辑 · 私有 iCloud 同步','syncTitle':'多端同时改，\n正文自动合并。','syncIntro':'手机补一条待办，Mac 改一段计划。即使同时编辑，普通笔记的正文改动也会在同步后汇合，减少来回挑选冲突副本的麻烦。',
  'syncMark':'自己的设备 · 同一 Apple 账户 · 按需开启',
  'ordinaryTitle':'普通笔记，改动自动合到一起。','ordinaryBody':'在登录同一 Apple 账户的设备上开启 iCloud 同步，正文的并发改动会自动合并。没网也能先写，重新连网后继续同步。新安装默认关闭同步。',
  'encryptedTitle':'加密笔记，不同版本都留好。','encryptedBody':'加密笔记的并发改动保留为独立密文版本。解锁后查看、选择和恢复所需内容；标题及部分外层信息仍可见。',
  'platformTitle':'每台设备，各有所长。','platformCaption':'三端共享写作基础，Mac 另有更完整的资料处理工具。','platformHeads':['能力','Mac','iPhone 与 iPad'],
  'platformRows':[
   ['写作与整理','Markdown、表格、图表、公式、代码、文件夹与层级标签','Markdown、表格、图表、公式、代码、文件夹与层级标签'],
   ['查找','本地语义与关键词搜索、文内查找','关键词搜索、文内查找'],
   ['导入与分享','本地文档转换，以及 PDF、DOCX、ePub 等多格式导出','照片和文件附件；分享 Markdown 或笔记附件包'],
   ['主题外观','22 套主题、自定义配色，以及主题文件导入导出','22 套主题，可搭配字体与版式设置'],
   ['继续写作','按需开启 iCloud，与自己的设备同步','按需开启 iCloud，与自己的设备同步']],
  'supportEyebrow':'需要时，搭把手','supportTitle':'一些实用的答案。','supportIntro':'从写下第一篇，到找回某个细节。这里说明搜索、同步，以及你的数据如何处理。',
  'contactTitle':'遇到问题了？','contactBody':'使用问题或隐私疑问，可以直接发邮件。请说明设备、Zebra 版本、预期结果和实际情况；也可以在 GitHub 提交公开反馈。','contactAction':'提交公开反馈 ↗','emailAction':'邮件联系','emailFooter':'联系我们','privacyContactTitle':'支持与隐私联系','privacyContactBody':'使用 Zebra 遇到问题，或对数据处理方式有疑问，可以通过以下邮箱联系我们。',
  'footer':'让想法，自然成篇。','source':'GitHub','close':'关闭截图','noScript':'关闭 JavaScript 时仍可浏览 Mac 截图和帮助内容。开启后可切换设备、查看大图。',
  'privacyTitle':'隐私与数据 — Zebra','privacyType':'产品数据处理说明','back':'返回 Zebra','githubPrivacy':'GitHub 隐私声明',
 }
}

def paragraphs(text):
 return ''.join(f'<p>{E(p)}</p>' for p in text.split('\n\n'))

def poster_url(path, prefix=''):
 return f"{prefix}{path}?v={POSTER_ASSETS[path]['sha256'][:12]}"

def film(locale, prefix):
 """The promo film starts paused with native controls; site.js plays it
 muted while it is on screen unless the reader prefers reduced motion."""
 video=VIDEOS.get(locale)
 if not video:return ''
 f=FILM[locale]
 src=f"{prefix}{video['path']}?v={video['sha256'][:12]}"; poster=f"{prefix}{video['poster']['path']}?v={video['poster']['sha256'][:12]}"
 return (f'<section class="film" id="film" aria-labelledby="film-title"><p class="eyebrow">{E(f["eyebrow"])}</p><h2 id="film-title">{E(f["title"])}</h2>'
  f'<div class="film-frame"><video id="promo-video" controls muted loop playsinline preload="none" poster="{poster}" width="{video["width"]}" height="{video["height"]}" aria-label="{E(f["label"])}" aria-describedby="film-caption"><source src="{src}" type="video/mp4"></video>'
  f'<button class="film-toggle" type="button" hidden data-play-label="{E(f["play"])}" data-pause-label="{E(f["pause"])}" aria-label="{E(f["play"])}"><span aria-hidden="true"></span></button></div>'
  f'<p class="film-caption" id="film-caption">{E(f["caption"])}</p></section>')

def page(locale, privacy=False):
 u=UI[locale]; zh=locale=='zh-Hans'; pre='../' if zh else ''; home='index.html'; filename='privacy.html' if privacy else 'index.html'; path=('zh/' if zh else '')+filename
 other=('../'+filename) if zh else ('zh/'+filename); canonical=BASE+path
 title=u['privacyTitle'] if privacy else u['title']
 email=E(SUPPORT['contact']['email']); email_link=f'<a href="mailto:{email}">{email}</a>'
 social_image=poster_url(f'assets/images/macos/{locale}/01-write-large.webp', BASE)
 head=f'''<!doctype html>
<html lang="{u['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><meta name="theme-color" content="#faf7f0"><meta name="referrer" content="strict-origin-when-cross-origin"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'">
<title>{E(title)}</title><meta name="description" content="{E(u['description'])}"><link rel="canonical" href="{canonical}"><link rel="alternate" hreflang="en" href="{BASE}{filename}"><link rel="alternate" hreflang="zh-Hans" href="{BASE}zh/{filename}"><link rel="alternate" hreflang="x-default" href="{BASE}{filename}"><meta property="og:type" content="website"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(u['description'])}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{social_image}"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="{pre}assets/images/icon.png"><link rel="apple-touch-icon" href="{pre}assets/images/icon.png"><link rel="stylesheet" href="{pre}assets/site.css"><script defer src="{pre}assets/site.js"></script></head><body>
<a class="skip-link" href="#main">{u['skip']}</a><div class="container"><header class="site-header"><a class="brand" href="{home}" aria-label="Zebra {u['home']}"><img src="{pre}assets/images/icon.png" width="42" height="42" alt="">zebra</a><nav class="site-nav" aria-label="{'主导航' if zh else 'Main navigation'}"><a class="nav-extra" href="{home}#explore">{u['features']}</a><a class="nav-extra" href="{home}#sync">{u['sync']}</a><a href="{home}#support">{u['support']}</a><a class="language" href="{other}" lang="{'en' if zh else 'zh-Hans'}" hreflang="{'en' if zh else 'zh-Hans'}">{u['other']}</a></nav></header>'''
 footer=f'''<footer class="site-footer"><div><span class="footer-brand">zebra</span> &nbsp; {u['footer']}</div><nav class="footer-links" aria-label="{'页脚导航' if zh else 'Footer navigation'}"><a href="{home}#support">{u['support']}</a><a href="privacy.html">{u['privacy']}</a><a href="mailto:{email}">{u['emailFooter']}</a><a href="{SUPPORT['contact']['repositoryURL']}">{u['source']} ↗</a></nav></footer></div></body></html>'''
 if privacy:
  d=SUPPORT['locales'][locale]['privacy']; sections=''.join(f'<section id="{x["id"]}"><h2>{E(x["title"])}</h2>'+''.join(f'<p>{E(t)}</p>' for t in x['paragraphs'])+'</section>' for x in d['sections'])
  body=f'''<main id="main" class="document"><p class="eyebrow">{E(d['eyebrow'])}</p><h1>{E(d['title'])}</h1><p class="lead">{E(d['intro'])}</p><p class="notice">{E(d['documentType'])}<br>{E(d['lastReviewedLabel'])}</p>{sections}<p><a href="{SUPPORT['externalLinks'][0]['url']}">{u['githubPrivacy']} ↗</a></p><section id="privacy-contact"><h2>{u['privacyContactTitle']}</h2><p>{u['privacyContactBody']}</p><p>{email_link}</p></section><a class="button secondary" href="{home}">← {u['back']}</a></main>'''
  return head+body+footer
 devices={}; sizes={'macos':(2880,1800),'iphone':(1206,2622),'ipad':(2752,2064)}
 for platform in ['macos','iphone','ipad']:
  w,h=sizes[platform]; cards=[]
  for i,c in enumerate(FEATURES[platform][locale],1):
   stem=f'assets/images/{platform}/{locale}/{i:02}-{c["id"]}'
   cards.append(dict(headline=c['headline'],summary=c['subheadline'],small=poster_url(stem+'-small.webp',pre),large=poster_url(stem+'-large.webp',pre),smallWidth=720,largeWidth=min(1440,w),width=w,height=h,alt=f'{c["headline"]} — Zebra '+{'macos':'Mac','iphone':'iPhone','ipad':'iPad'}[platform]))
  devices[platform]=cards
 cards_html=''
 for i,c in enumerate(devices['macos'],1):
  cards_html+=f'''<article class="feature"><button class="feature-image" type="button" data-large="{c['large']}" aria-label="{E(u['view']+' '+c['headline'])}"><img src="{c['small']}" srcset="{c['small']} 720w, {c['large']} 1440w" sizes="(max-width: 700px) 94vw, 46vw" width="{c['width']}" height="{c['height']}" alt="{E(c['alt'])}" loading="lazy" decoding="async"><span class="zoom-indicator" aria-hidden="true">↗</span></button><div class="feature-copy"><div class="feature-top"><span class="feature-index">{i:02}</span><h3>{E(c['headline'])}</h3></div><p>{E(c['summary'])}</p></div></article>'''
 data=dict(devices=devices,viewLabel=u['view'],deviceLabels={'macos':'Mac','iphone':'iPhone','ipad':'iPad'},statusText=u['status'])
 serial=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
 hero=devices['macos'][0]
 faq=''.join(f'<details id="faq-{x["id"]}"><summary>{E(x["question"])}</summary><div>{paragraphs(x["answer"])}</div></details>' for x in SUPPORT['locales'][locale]['faqs'])
 table='<thead><tr>'+''.join(f'<th scope="col">{E(t)}</th>' for t in u['platformHeads'])+'</tr></thead><tbody>'+''.join('<tr><th scope="row">'+E(r[0])+'</th>'+''.join(f'<td>{E(t)}</td>' for t in r[1:])+'</tr>' for r in u['platformRows'])+'</tbody>'
 body=f'''<main id="main"><section class="hero"><div><p class="eyebrow">{u['eyebrow']}</p><h1>{E(u['hero']).replace(chr(10),'<br>')}</h1><p class="lead">{u['lead']}</p><div class="actions"><a class="button" href="#explore">{u['explore']} <span aria-hidden="true">↓</span></a><a class="button secondary" href="#support">{u['help']}</a></div></div><div><a class="hero-image-link" href="#explore" aria-label="{u['explore']}"><div class="poster"><img src="{hero['large']}" srcset="{hero['small']} 720w, {hero['large']} 1440w" sizes="(max-width: 700px) 94vw, 55vw" width="2880" height="1800" alt="{E(hero['alt'])}" fetchpriority="high"></div></a><p class="hero-caption">{u['caption']}</p></div></section>
<div class="principles">{''.join('<span>'+E(p)+'</span>' for p in u['principles'])}</div>
{film(locale,pre)}
<section id="explore"><div class="section-heading"><div><p class="eyebrow">{u['galleryEyebrow']}</p><h2>{u['galleryTitle']}</h2><p>{u['galleryIntro']}</p></div><div class="device-switch" role="group" aria-label="{'选择设备' if zh else 'Choose a device'}"><button type="button" data-device-button="macos" aria-pressed="true">Mac</button><button type="button" data-device-button="iphone" aria-pressed="false">iPhone</button><button type="button" data-device-button="ipad" aria-pressed="false">iPad</button></div></div><p id="gallery-status" class="eyebrow" aria-live="polite">Mac · {u['status']}</p><noscript><p class="no-script">{u['noScript']}</p></noscript><div id="gallery" class="gallery" data-device="macos">{cards_html}</div><p class="gallery-note">{u['galleryNote']}</p></section>
<section id="sync" class="sync-section"><div><p class="eyebrow">{u['syncEyebrow']}</p><h2>{E(u['syncTitle']).replace(chr(10),'<br>')}</h2><p>{u['syncIntro']}</p><span class="sync-mark">{u['syncMark']}</span></div><div><div class="sync-card"><h3>{u['ordinaryTitle']}</h3><p>{u['ordinaryBody']}</p></div><div class="sync-card"><h3>{u['encryptedTitle']}</h3><p>{u['encryptedBody']}</p></div></div></section>
<section class="platforms"><h2>{u['platformTitle']}</h2><table class="platform-table"><caption>{u['platformCaption']}</caption>{table}</table></section>
<section class="support" id="support"><div class="intro"><p class="eyebrow">{u['supportEyebrow']}</p><h2>{u['supportTitle']}</h2><p>{u['supportIntro']}</p><a href="privacy.html">{u['privacy']} ↗</a></div><div class="faq">{faq}</div></section>
<section class="contact" id="contact"><div><h2>{u['contactTitle']}</h2><p>{u['contactBody']}</p><p class="contact-email">{email_link}</p></div><div class="contact-options"><a class="button" href="mailto:{email}">{u['emailAction']}</a><a class="button secondary" href="{SUPPORT['contact']['publicIssueURL']}">{u['contactAction']}</a></div></section></main>
<dialog id="poster-dialog" class="poster-dialog" aria-labelledby="dialog-title"><div class="dialog-bar"><h2 id="dialog-title"></h2><button id="dialog-close" type="button" aria-label="{u['close']}">×</button></div><img id="dialog-image" alt=""></dialog><script id="gallery-data" type="application/json">{serial}</script>'''
 return head+body+footer

for locale in UI:
 directory=ROOT/('zh' if locale=='zh-Hans' else '')
 directory.mkdir(exist_ok=True)
 for is_privacy in (False,True):
  (directory/('privacy.html' if is_privacy else 'index.html')).write_text(page(locale,is_privacy))
print('Built four static pages: English / Simplified Chinese, home / privacy and data.')
