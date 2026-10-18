#!/usr/bin/env python3
"""Generate the buildless, four-language GitHub Pages site from reviewed copy.

  python3 scripts/build.py               build the eight pages
  python3 scripts/build.py --sync-copy   first copy the feature cards from the App Store copy.json

Images come from asset-manifest.json (written by scripts/derive_images.js). A device
group is shown in a language only when its full set of scenes exists; a language
without its own set shows the English set with a visible note, and a device with no
complete set at all is left out of the page.
"""
from pathlib import Path
import argparse
import html
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://entropysniper-app.github.io/zebra.app/'
FEATURES_PATH = ROOT / 'content/features.json'
# The App Store copy source of truth; present when this repository is the Zebra checkout's `Website` submodule.
APP_STORE_COPY = ROOT.parent / 'AppStoreSubmission/refresh-2026-10-11/copy.json'
COPY_PLATFORMS = ['macos', 'iphone', 'ipad']
# Site languages in switcher order. Keys are the App Store locale codes used by content/ and image paths;
# `lang` is both the html lang and the hreflang value.
LOCALES = {
 'en-US': {'dir': '', 'lang': 'en', 'name': 'English', 'og': 'en_US'},
 'zh-Hans': {'dir': 'zh/', 'lang': 'zh-Hans', 'name': '简体中文', 'og': 'zh_CN'},
 'ja': {'dir': 'ja/', 'lang': 'ja', 'name': '日本語', 'og': 'ja_JP'},
 'fr-FR': {'dir': 'fr/', 'lang': 'fr', 'name': 'Français', 'og': 'fr_FR'},
}
# The x-default page, and the image and film set shown while a translation's own set is missing.
FALLBACK_LOCALE = 'en-US'
# Gallery device groups in tab order. `copy` is the features.json platform whose cards caption the
# posters: the iPhone Duo inner-display posters are rendered from the iPhone copy.
DEVICES = [
 {'id': 'macos', 'label': 'Mac', 'copy': 'macos'},
 {'id': 'iphone', 'label': 'iPhone', 'copy': 'iphone'},
 {'id': 'ipad', 'label': 'iPad', 'copy': 'ipad'},
 {'id': 'iphone-duo', 'label': 'iPhone Duo', 'copy': 'iphone'},
]
PAGES = ['index.html', 'privacy.html']
FILM = {
 'en-US': {'eyebrow':'Zebra in 14 seconds','title':'Watch an idea take shape.','caption':'Every app screen in this film is a real Zebra capture; the moving type is added for the film.','fallback':' The film’s text is in English.','play':'Play video','pause':'Pause video','label':'Zebra promo film'},
 'zh-Hans': {'eyebrow':'14 秒认识 Zebra','title':'看一个想法慢慢成形。','caption':'片中 App 画面均为 Zebra 真实截图，动态文字为短片另加。','fallback':'片中文字为英文。','play':'播放视频','pause':'暂停视频','label':'Zebra 宣传短片'},
 'ja': {'eyebrow':'14秒でわかるZebra','title':'アイデアが、かたちになるまで。','caption':'この映像のアプリ画面はすべてZebraの実際の画面です。動くテキストは映像用に加えたものです。','fallback':'映像内のテキストは英語です。','play':'動画を再生','pause':'動画を一時停止','label':'Zebraの紹介映像'},
 'fr-FR': {'eyebrow':'Zebra en 14 secondes','title':'Regardez une idée prendre forme.','caption':'Chaque écran de l’app dans ce film est une vraie capture de Zebra ; les textes animés ont été ajoutés pour le film.','fallback':' Ils sont en anglais.','play':'Lire la vidéo','pause':'Mettre la vidéo en pause','label':'Film de présentation de Zebra'},
}
E = html.escape
UI = {
 'en-US': {
  'skip':'Skip to content','features':'Explore','sync':'Sync','support':'Support','privacy':'Privacy & data','home':'Home',
  'mainNav':'Main navigation','footerNav':'Footer navigation','languageLabel':'Language:','chooseDevice':'Choose a device',
  'title':'Zebra — Markdown notes, diagrams, math & more','description':'A native Markdown notebook for Mac, iPhone and iPad. Write, organize, find and carry your ideas across your own devices. Explore Zebra and get support.',
  'eyebrow':'Markdown notes · Mac, iPhone & iPad','hero':'Type Markdown.\nGive ideas their full shape.','lead':'Type the syntax. See it formatted. Add diagrams, math, code, and editable tables as your ideas grow—from a quick note to a piece worth sharing.',
  'explore':'Meet Zebra','help':'Get help','caption':'Zebra on Mac · fictional notes, real app screenshots','imageFallbackShort':'English screenshots',
  'principles':['Native Markdown writing','Your notes, local by default','Optional iCloud sync'],
  'galleryEyebrow':'A little note. A bigger picture.','galleryTitle':'More ways to make yourself clear.','galleryIntro':'Start with a sentence. Add the details that make it yours. Choose a device to see what Zebra can do there.',
  'view':'View screenshot:','status':'10 features','imageFallback':'Screenshots in this language are on their way; the English screenshots are shown for this device.','galleryNote':'Real app screens with sample notes. The zebra is our illustrated window companion. The sync diagram explains the strategy; it is not a live sync recording.',
  'syncEyebrow':'Concurrent editing · Private iCloud sync','syncTitle':'Your edits merge\nautomatically.','syncIntro':'Add a task on iPhone while revising a plan on Mac. Concurrent edits to note text merge when you sync, reducing the work of choosing between conflict copies.',
  'syncMark':'Your devices · Same Apple Account · Your choice',
  'ordinaryTitle':'Your notes: edits come together.','ordinaryBody':'Enable iCloud sync on devices signed in to the same Apple Account. Concurrent changes to note text merge automatically. Write offline and sync when you reconnect. Sync is off by default on new installations.',
  'passwordTitle':'Notes with a password: synced the same way.','passwordBody':'A note password hides the note in Zebra until you enter it. It is not encryption: the content syncs and merges like any other note. Only a password check and an optional hint sync with it, never the password itself.',
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
  'skip':'跳到正文','features':'功能','sync':'同步','support':'支持','privacy':'隐私与数据','home':'首页',
  'mainNav':'主导航','footerNav':'页脚导航','languageLabel':'语言：','chooseDevice':'选择设备',
  'title':'Zebra — Markdown 笔记、图表、公式与代码','description':'为 Mac、iPhone 和 iPad 打造的原生 Markdown 笔记。写作、整理、找回线索，在自己的设备间接着写。了解 Zebra 的功能与使用帮助。',
  'eyebrow':'Markdown 笔记 · Mac、iPhone 与 iPad','hero':'直接写 Markdown，\n把想法写完整。','lead':'敲下语法，看到排版。标题、列表、代码块直接输入，图表、公式与可编辑表格接着补上。从随手记一句，到认真写一篇，都在 Zebra。',
  'explore':'认识 Zebra','help':'获取帮助','caption':'Mac 上的 Zebra · 虚构演示内容，真实 App 界面','imageFallbackShort':'英文版截图',
  'principles':['原生 Markdown 写作','笔记默认留在本机','按需开启 iCloud 同步'],
  'galleryEyebrow':'从一句话，到一套想法','galleryTitle':'让表达，多几种可能。','galleryIntro':'从文字开始，慢慢补全细节。选择你的设备，看看 Zebra 如何承载不同的想法。',
  'view':'查看截图：','status':'10 个使用场景','imageFallback':'该设备的简体中文截图正在准备中，暂以英文截图展示。','galleryNote':'画面来自真实 App，笔记为演示内容。趴窗斑马是独立插画；同步图用于解释机制，并非实时同步录像。',
  'syncEyebrow':'多端并发编辑 · 私有 iCloud 同步','syncTitle':'多端同时改，\n正文自动合并。','syncIntro':'手机补一条待办，Mac 改一段计划。即使同时编辑，笔记的正文改动也会在同步后汇合，减少来回挑选冲突副本的麻烦。',
  'syncMark':'自己的设备 · 同一 Apple 账户 · 按需开启',
  'ordinaryTitle':'你的笔记，改动自动合到一起。','ordinaryBody':'在登录同一 Apple 账户的设备上开启 iCloud 同步，正文的并发改动会自动合并。没网也能先写，重新连网后继续同步。新安装默认关闭同步。',
  'passwordTitle':'设有密码的笔记，也同样同步。','passwordBody':'笔记密码让 Zebra 在你输入密码前不显示这篇笔记，但它不是加密：内容与其他笔记一样同步、合并。随笔记同步的只有密码校验值和可选提示，不包括密码本身。',
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
 },
 'ja': {
  'skip':'本文へスキップ','features':'機能','sync':'同期','support':'サポート','privacy':'プライバシーとデータ','home':'ホーム',
  'mainNav':'メインナビゲーション','footerNav':'フッターナビゲーション','languageLabel':'言語：','chooseDevice':'デバイスを選択',
  'title':'Zebra — 図も数式もコードも書けるMarkdownノート','description':'Mac、iPhone、iPadのためのネイティブなMarkdownノート。書いて、整理して、見つけて、自分のデバイスで続きを書けます。Zebraの機能とサポート情報をご覧ください。',
  'eyebrow':'Markdownノート · Mac、iPhone、iPad','hero':'Markdownで書く。\nアイデアを、かたちに。','lead':'記法を入力すれば、その場で整形。アイデアが育つにつれて、図、数式、コード、編集できる表を加えていけます。さっと書いた一行から、人に届けたい文章まで。',
  'explore':'Zebraを知る','help':'サポートを見る','caption':'Mac版Zebra · 架空のノートと実際のアプリ画面','imageFallbackShort':'英語版の画面',
  'principles':['ネイティブなMarkdown執筆','ノートは標準でデバイス内に','iCloud同期は必要なときに'],
  'galleryEyebrow':'小さなノートから、大きな全体像へ','galleryTitle':'伝えたいことを、もっと明快に。','galleryIntro':'ひとつの文から始めて、自分らしい細部を加えていく。デバイスを選んで、Zebraでできることをご覧ください。',
  'view':'スクリーンショットを表示：','status':'10のシーン','imageFallback':'このデバイスの日本語版スクリーンショットは準備中のため、英語版を表示しています。','galleryNote':'画面は実際のアプリで、ノートはサンプルです。窓辺のシマウマはイラストのキャラクターです。同期の図は仕組みを説明するもので、実際の同期を記録したものではありません。',
  'syncEyebrow':'同時編集 · プライベートなiCloud同期','syncTitle':'同時に編集しても、\n本文は自動で統合。','syncIntro':'iPhoneでタスクを書き足しながら、Macで計画を見直す。ノート本文への同時編集は同期するときに統合されるので、競合コピーを見比べて選ぶ手間が減ります。',
  'syncMark':'自分のデバイス · 同じAppleアカウント · オンにするかは自由',
  'ordinaryTitle':'ノートの変更は、ひとつに。','ordinaryBody':'同じAppleアカウントでサインインしたデバイスでiCloud同期をオンにすると、ノート本文への同時の変更は自動で統合されます。オフラインでも書けて、再接続すると同期されます。新規インストールでは、同期はオフになっています。',
  'passwordTitle':'パスワード付きのノートも、同じように同期。','passwordBody':'ノートのパスワードは、入力するまでZebraでノートを表示しないためのもので、暗号化ではありません。内容はほかのノートと同じように同期・統合されます。一緒に同期されるのはパスワード照合値と任意のヒントだけで、パスワードそのものは同期されません。',
  'platformTitle':'どのデバイスでも、しっくりと。','platformCaption':'書くための基本はどのデバイスでも同じ。Macにはさらにツールがそろっています。','platformHeads':['機能','Mac','iPhone・iPad'],
  'platformRows':[
   ['書く・整理する','Markdown、表、図、数式、コード、フォルダ、階層タグ','Markdown、表、図、数式、コード、フォルダ、階層タグ'],
   ['探す','ローカルの意味検索（中国語・英語）とキーワード検索、ノート内検索','キーワード検索、ノート内検索'],
   ['取り込む・書き出す','書類をローカルで変換、PDF・DOCX・ePubなどへの書き出し','写真・ファイルの添付、Markdownまたは添付ファイルごと共有'],
   ['外観','22種類のテーマ、カスタムカラー、テーマファイルの読み込み・書き出し','22種類のテーマ、フォントとレイアウトの設定'],
   ['続きを書く','自分のデバイスとのiCloud同期（オプション）','自分のデバイスとのiCloud同期（オプション）']],
  'supportEyebrow':'困ったときは','supportTitle':'よくある質問と答え。','supportIntro':'最初のノートから、もう一度見つけたい細部まで。書くこと、検索、同期、そしてデータの扱いについてご説明します。',
  'contactTitle':'うまくいかないときは','contactBody':'使い方やプライバシーについてのご質問は、メールでお問い合わせください。お使いのデバイス、Zebraのバージョン、期待した動作と実際に起きたことをお書き添えください。GitHubで公開の問題を報告することもできます。','contactAction':'公開の問題を報告 ↗','emailAction':'メールで問い合わせる','emailFooter':'お問い合わせ','privacyContactTitle':'サポートとプライバシーに関するお問い合わせ','privacyContactBody':'Zebraの使い方や、データの取り扱いについてのご質問は、以下のメールアドレスまでお問い合わせください。',
  'footer':'アイデアが生まれる、そのままのかたちで。','source':'GitHub','close':'スクリーンショットを閉じる','noScript':'JavaScriptがオフでも、Macのスクリーンショットとサポート情報をご覧いただけます。デバイスの切り替えや拡大表示にはJavaScriptをオンにしてください。',
  'privacyTitle':'プライバシーとデータ — Zebra','privacyType':'製品のデータ取り扱いに関する説明','back':'Zebraに戻る','githubPrivacy':'GitHubプライバシーステートメント',
 },
 'fr-FR': {
  'skip':'Aller au contenu','features':'Découvrir','sync':'Synchronisation','support':'Assistance','privacy':'Confidentialité et données','home':'Accueil',
  'mainNav':'Navigation principale','footerNav':'Navigation de pied de page','languageLabel':'Langue :','chooseDevice':'Choisir un appareil',
  'title':'Zebra — Notes Markdown, diagrammes, formules et plus','description':'Un carnet Markdown natif pour Mac, iPhone et iPad. Écrivez, classez et retrouvez vos idées, puis emportez-les sur vos propres appareils. Découvrez Zebra et obtenez de l’aide.',
  'eyebrow':'Notes Markdown · Mac, iPhone et iPad','hero':'Tapez du Markdown.\nDonnez forme à vos idées.','lead':'Tapez la syntaxe, voyez la mise en forme. Ajoutez diagrammes, formules, code et tableaux modifiables à mesure que vos idées grandissent — de la note rapide au texte digne d’être partagé.',
  'explore':'Découvrir Zebra','help':'Obtenir de l’aide','caption':'Zebra sur Mac · notes fictives, vraies captures de l’app','imageFallbackShort':'images en anglais',
  'principles':['Écriture Markdown native','Vos notes, en local par défaut','Synchronisation iCloud facultative'],
  'galleryEyebrow':'D’une petite note à une vue d’ensemble','galleryTitle':'Plus de façons de vous exprimer clairement.','galleryIntro':'Commencez par une phrase, puis ajoutez les détails qui la rendent vôtre. Choisissez un appareil pour voir ce que Zebra y permet.',
  'view':'Voir la capture :','status':'10 fonctionnalités','imageFallback':'Les captures en français pour cet appareil arrivent bientôt ; les captures en anglais sont affichées en attendant.','galleryNote':'Écrans réels de l’app avec des notes d’exemple. Le zèbre est notre compagnon illustré. Le schéma de synchronisation explique le principe ; ce n’est pas l’enregistrement d’une synchronisation réelle.',
  'syncEyebrow':'Édition simultanée · Synchronisation iCloud privée','syncTitle':'Vos modifications\nfusionnent automatiquement.','syncIntro':'Ajoutez une tâche sur l’iPhone pendant que vous révisez un plan sur le Mac. Les modifications simultanées du texte des notes fusionnent à la synchronisation, et vous avez moins de copies en conflit à départager.',
  'syncMark':'Vos appareils · Même compte Apple · À votre choix',
  'ordinaryTitle':'Vos notes : les modifications se rejoignent.','ordinaryBody':'Activez la synchronisation iCloud sur les appareils connectés au même compte Apple. Les modifications simultanées du texte des notes fusionnent automatiquement. Écrivez hors ligne, la synchronisation reprend à la reconnexion. La synchronisation est désactivée par défaut sur une nouvelle installation.',
  'passwordTitle':'Notes protégées par mot de passe : même synchronisation.','passwordBody':'Le mot de passe d’une note la masque dans Zebra jusqu’à ce que vous le saisissiez. Ce n’est pas un chiffrement : le contenu se synchronise et fusionne comme celui de toute autre note. Seuls une vérification du mot de passe et un indice facultatif l’accompagnent, jamais le mot de passe lui-même.',
  'platformTitle':'À l’aise sur chaque appareil.','platformCaption':'Les mêmes bases d’écriture partout, avec des outils en plus sur Mac.','platformHeads':['Fonction','Mac','iPhone et iPad'],
  'platformRows':[
   ['Écrire et classer','Markdown, tableaux, diagrammes, formules, code, dossiers et tags imbriqués','Markdown, tableaux, diagrammes, formules, code, dossiers et tags imbriqués'],
   ['Retrouver','Recherche sémantique locale (chinois et anglais) et par mots-clés, recherche dans la note','Recherche par mots-clés et dans la note'],
   ['Importer et exporter','Conversion locale de documents, exports PDF, DOCX, ePub et plus','Photos et fichiers joints ; partage en Markdown ou avec les pièces jointes'],
   ['Apparence','22 thèmes, couleurs personnalisées, import et export de fichiers de thème','22 thèmes, avec réglages de typographie et de mise en page'],
   ['Continuer d’écrire','Synchronisation iCloud facultative avec vos propres appareils','Synchronisation iCloud facultative avec vos propres appareils']],
  'supportEyebrow':'Un coup de main','supportTitle':'Quelques réponses utiles.','supportIntro':'De la première note au détail à retrouver. Voici comment fonctionnent l’écriture, la recherche, la synchronisation et vos données.',
  'contactTitle':'Quelque chose ne va pas ?','contactBody':'Écrivez-nous pour obtenir de l’aide ou poser une question sur la confidentialité. Indiquez votre appareil, la version de Zebra, ce que vous attendiez et ce qui s’est passé. Vous pouvez aussi signaler un problème public sur GitHub.','contactAction':'Signaler un problème public ↗','emailAction':'Écrire à l’assistance','emailFooter':'Nous écrire','privacyContactTitle':'Assistance et confidentialité','privacyContactBody':'Pour obtenir de l’aide sur Zebra ou poser une question sur le traitement de vos données, écrivez-nous à l’adresse ci-dessous.',
  'footer':'Pensé pour la façon dont naissent les idées.','source':'GitHub','close':'Fermer la capture','noScript':'Ces captures Mac et l’assistance restent accessibles sans JavaScript. Activez JavaScript pour changer d’appareil et agrandir les images.',
  'privacyTitle':'Confidentialité et données — Zebra','privacyType':'Informations sur le traitement des données du produit','back':'Retour à Zebra','githubPrivacy':'Déclaration de confidentialité de GitHub',
 },
}
GLOBE = ('<svg class="globe" aria-hidden="true" focusable="false" viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.3">'
 '<circle cx="8" cy="8" r="6.4"/><path d="M1.6 8h12.8M8 1.6c1.9 2 2.8 4.1 2.8 6.4S9.9 12.4 8 14.4M8 1.6C6.1 3.6 5.2 5.7 5.2 8s.9 4.4 2.8 6.4"/></svg>')


def fail(message):
 sys.exit(f'build.py: {message}')


def read_json(path):
 return json.loads(path.read_text())


def write_json(path, data):
 path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def copy_drift(features, copy):
 """Feature-card fields where content/features.json differs from the App Store copy.json."""
 changes = []
 for platform in COPY_PLATFORMS:
  for locale in LOCALES:
   source = copy['platforms'][platform]['locales'].get(locale, {}).get('cards')
   if source is None:
    changes.append(f'{platform}/{locale}: missing from copy.json'); continue
   site = features.get(platform, {}).get(locale)
   if site is None:
    changes.append(f'{platform}/{locale}: not yet in features.json'); continue
   for i, (a, b) in enumerate(zip(site, source)):
    for key in sorted(set(a) | set(b)):
     if a.get(key) != b.get(key):
      changes.append(f'{platform}/{locale}/{b.get("id", i)}.{key}: {json.dumps(a.get(key), ensure_ascii=False)} → {json.dumps(b.get(key), ensure_ascii=False)}')
   if len(site) != len(source):
    changes.append(f'{platform}/{locale}: {len(site)} cards here, {len(source)} in copy.json')
 return changes


def sync_copy(path):
 """Copy every site locale's cards from copy.json, listing each changed field."""
 copy = read_json(path); features = read_json(FEATURES_PATH)
 changes = copy_drift(features, copy)
 for platform in COPY_PLATFORMS:
  for locale in LOCALES:
   cards = copy['platforms'][platform]['locales'].get(locale, {}).get('cards')
   if cards is None: fail(f'{path} has no platforms.{platform}.locales.{locale}.cards')
   features.setdefault(platform, {})[locale] = cards
 write_json(FEATURES_PATH, features)
 print(f'Synced feature cards from {path.name}: ' + (f'{len(changes)} change(s)' if changes else 'no changes'))
 for line in changes: print('  ' + line)


def check_sources(features, support):
 """Every language has complete chrome, film, support and card copy in one scene order."""
 problems = []
 for name, table in (('UI', UI), ('FILM', FILM)):
  for locale in LOCALES:
   if locale not in table: problems.append(f'{name} lacks {locale}'); continue
   missing = set(table[FALLBACK_LOCALE]) - set(table[locale])
   if missing: problems.append(f'{name}[{locale}] lacks {sorted(missing)}')
 scenes = [card['id'] for card in features['macos'][FALLBACK_LOCALE]]
 for platform in COPY_PLATFORMS:
  for locale in LOCALES:
   cards = features.get(platform, {}).get(locale)
   if cards is None: problems.append(f'features.json lacks {platform}/{locale}')
   elif [card['id'] for card in cards] != scenes: problems.append(f'features.json {platform}/{locale} scenes differ from {scenes}')
 for locale in LOCALES:
  if locale not in support['locales']: problems.append(f'support.json lacks {locale}')
 for link in support['externalLinks']:
  problems += [f'support.json link {link["id"]} lacks a {locale} label' for locale in LOCALES if locale not in link['label']]
 if problems: fail('incomplete source copy:\n  ' + '\n  '.join(problems))
 return scenes


def complete_image_sets(manifest, scenes):
 """(device, locale) → posters by scene, for sets whose every scene has both derivatives on disk."""
 sets = {}
 for poster in manifest['posters']:
  if all((ROOT / variant['path']).is_file() for variant in poster['variants'].values()):
   sets.setdefault((poster['platform'], poster['locale']), {})[poster['scene']] = poster
 return {key: posters for key, posters in sets.items() if all(scene in posters for scene in scenes)}


def load():
 """Read and check the copy and image manifest that the page templates use."""
 global FEATURES, SUPPORT, MANIFEST, SCENES, VIDEOS, IMAGE_SETS
 FEATURES = read_json(FEATURES_PATH)
 SUPPORT = read_json(ROOT / 'content/support.json')
 MANIFEST = read_json(ROOT / 'asset-manifest.json')
 SCENES = check_sources(FEATURES, SUPPORT)
 VIDEOS = {video['locale']: video for video in MANIFEST.get('videos', [])}
 IMAGE_SETS = complete_image_sets(MANIFEST, SCENES)


def image_locale(device, locale):
 """The page's own poster set when complete, else the English set; None leaves the device out."""
 return next((candidate for candidate in (locale, FALLBACK_LOCALE) if (device, candidate) in IMAGE_SETS), None)


def versioned(asset, prefix=''):
 return f"{prefix}{asset['path']}?v={asset['sha256'][:12]}"


def paragraphs(text):
 return ''.join(f'<p>{E(p)}</p>' for p in text.split('\n\n'))


def film(locale, prefix):
 """The promo film starts paused with native controls; site.js plays it muted while it is on
 screen unless the reader prefers reduced motion. A language without its own film shows the English one."""
 video = VIDEOS.get(locale) or VIDEOS.get(FALLBACK_LOCALE)
 if not video: return ''
 f = FILM[locale]
 caption = f['caption'] if video['locale'] == locale else f['caption'] + f['fallback']  # each language's own separator
 return (f'<section class="film" id="film" aria-labelledby="film-title"><p class="eyebrow">{E(f["eyebrow"])}</p><h2 id="film-title">{E(f["title"])}</h2>'
  f'<div class="film-frame"><video id="promo-video" controls muted loop playsinline preload="none" poster="{versioned(video["poster"], prefix)}" width="{video["width"]}" height="{video["height"]}" aria-label="{E(f["label"])}" aria-describedby="film-caption"><source src="{versioned(video, prefix)}" type="video/mp4"></video>'
  f'<button class="film-toggle" type="button" hidden data-play-label="{E(f["play"])}" data-pause-label="{E(f["pause"])}" aria-label="{E(f["play"])}"><span aria-hidden="true"></span></button></div>'
  f'<p class="film-caption" id="film-caption">{E(caption)}</p></section>')


def language_menu(locale, filename, prefix):
 """A native disclosure listing the other languages by their own names; it needs no JavaScript."""
 me = LOCALES[locale]
 links = ''.join(f'<li><a href="{prefix}{other["dir"]}{filename}" lang="{other["lang"]}" hreflang="{other["lang"]}">{E(other["name"])}</a></li>'
                 for key, other in LOCALES.items() if key != locale)
 return (f'<details class="language-menu"><summary>{GLOBE}<span class="visually-hidden">{E(UI[locale]["languageLabel"])} </span>'
  f'<span lang="{me["lang"]}">{E(me["name"])}</span></summary><ul class="language-list">{links}</ul></details>')


def gallery(locale, prefix):
 """Cards per shown device, and which language's posters each device uses."""
 devices, image_locales = {}, {}
 for device in DEVICES:
  source = image_locale(device['id'], locale)
  if source is None: continue
  posters = IMAGE_SETS[(device['id'], source)]; cards = []
  for card in FEATURES[device['copy']][locale]:
   poster = posters[card['id']]; small, large = poster['variants']['small'], poster['variants']['large']
   cards.append(dict(headline=card['headline'], summary=card['subheadline'], small=versioned(small, prefix), large=versioned(large, prefix),
                     smallWidth=small['width'], largeWidth=large['width'], width=poster['source']['width'], height=poster['source']['height'],
                     alt=f"{card['headline']} — Zebra {device['label']}"))
  devices[device['id']] = cards; image_locales[device['id']] = source
 if 'macos' not in devices: fail('the Mac poster set is missing in every language; run scripts/derive_images.js')
 return devices, image_locales


def page(locale, filename):
 u = UI[locale]; me = LOCALES[locale]; pre = '../' if me['dir'] else ''; home = 'index.html'
 privacy = filename == 'privacy.html'; canonical = BASE + me['dir'] + filename
 title = u['privacyTitle'] if privacy else u['title']
 email = E(SUPPORT['contact']['email']); email_link = f'<a href="mailto:{email}">{email}</a>'
 devices, image_locales = gallery(locale, pre)
 social_image = BASE + devices['macos'][0]['large'][len(pre):]
 alternates = ''.join(f'<link rel="alternate" hreflang="{o["lang"]}" href="{BASE}{o["dir"]}{filename}">' for o in LOCALES.values())
 alternates += f'<link rel="alternate" hreflang="x-default" href="{BASE}{LOCALES[FALLBACK_LOCALE]["dir"]}{filename}">'
 og_locales = f'<meta property="og:locale" content="{me["og"]}">' + ''.join(f'<meta property="og:locale:alternate" content="{o["og"]}">' for key, o in LOCALES.items() if key != locale)
 head = f'''<!doctype html>
<html lang="{me['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><meta name="theme-color" content="#faf7f0"><meta name="referrer" content="strict-origin-when-cross-origin"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'">
<title>{E(title)}</title><meta name="description" content="{E(u['description'])}"><link rel="canonical" href="{canonical}">{alternates}<meta property="og:type" content="website"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(u['description'])}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{social_image}">{og_locales}<meta name="twitter:card" content="summary_large_image"><link rel="icon" href="{pre}assets/images/icon.png"><link rel="apple-touch-icon" sizes="180x180" href="{pre}assets/images/apple-touch-icon.png"><link rel="stylesheet" href="{pre}assets/site.css"><script defer src="{pre}assets/site.js"></script></head><body>
<a class="skip-link" href="#main">{E(u['skip'])}</a><div class="container"><header class="site-header"><a class="brand" href="{home}" aria-label="Zebra {E(u['home'])}"><img src="{pre}assets/images/icon.png" width="42" height="42" alt="">zebra</a><nav class="site-nav" aria-label="{E(u['mainNav'])}"><a class="nav-extra" href="{home}#explore">{E(u['features'])}</a><a class="nav-extra" href="{home}#sync">{E(u['sync'])}</a><a href="{home}#support">{E(u['support'])}</a>{language_menu(locale, filename, pre)}</nav></header>'''
 footer = f'''<footer class="site-footer"><div><span class="footer-brand">zebra</span> &nbsp; {E(u['footer'])}</div><nav class="footer-links" aria-label="{E(u['footerNav'])}"><a href="{home}#support">{E(u['support'])}</a><a href="privacy.html">{E(u['privacy'])}</a><a href="mailto:{email}">{E(u['emailFooter'])}</a><a href="{SUPPORT['contact']['repositoryURL']}">{E(u['source'])} ↗</a></nav></footer></div></body></html>'''
 if privacy:
  d = SUPPORT['locales'][locale]['privacy']
  sections = ''.join(f'<section id="{x["id"]}"><h2>{E(x["title"])}</h2>' + ''.join(f'<p>{E(t)}</p>' for t in x['paragraphs']) + '</section>' for x in d['sections'])
  body = f'''<main id="main" class="document"><p class="eyebrow">{E(d['eyebrow'])}</p><h1>{E(d['title'])}</h1><p class="lead">{E(d['intro'])}</p><p class="notice">{E(d['documentType'])}<br>{E(d['lastReviewedLabel'])}</p>{sections}<p><a href="{SUPPORT['externalLinks'][0]['url']}">{E(u['githubPrivacy'])} ↗</a></p><section id="privacy-contact"><h2>{E(u['privacyContactTitle'])}</h2><p>{E(u['privacyContactBody'])}</p><p>{email_link}</p></section><a class="button secondary" href="{home}">← {E(u['back'])}</a></main>'''
  return head + body + footer
 cards_html = ''
 for i, c in enumerate(devices['macos'], 1):
  cards_html += f'''<article class="feature"><button class="feature-image" type="button" data-large="{c['large']}" aria-label="{E(u['view']+' '+c['headline'])}"><img src="{c['small']}" srcset="{c['small']} {c['smallWidth']}w, {c['large']} {c['largeWidth']}w" sizes="(max-width: 700px) 94vw, 46vw" width="{c['width']}" height="{c['height']}" alt="{E(c['alt'])}" loading="lazy" decoding="async"><span class="zoom-indicator" aria-hidden="true">↗</span></button><div class="feature-copy"><div class="feature-top"><span class="feature-index">{i:02}</span><h3>{E(c['headline'])}</h3></div><p>{E(c['summary'])}</p></div></article>'''
 shown = [device for device in DEVICES if device['id'] in devices]
 data = dict(locale=locale, devices=devices, imageLocales=image_locales, viewLabel=u['view'], deviceLabels={d['id']: d['label'] for d in shown}, statusText=u['status'])
 serial = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
 buttons = ''.join(f'<button type="button" data-device-button="{d["id"]}" aria-pressed="{str(d["id"] == "macos").lower()}">{E(d["label"])}</button>' for d in shown)
 mac_fallback = image_locales['macos'] != locale
 fallback_note = f'<p id="gallery-fallback" class="gallery-fallback"{"" if mac_fallback else " hidden"}>{E(u["imageFallback"])}</p>' if any(source != locale for source in image_locales.values()) else ''
 caption = u['caption'] + (f" · {u['imageFallbackShort']}" if mac_fallback else '')
 hero = devices['macos'][0]
 faq = ''.join(f'<details id="faq-{x["id"]}"><summary>{E(x["question"])}</summary><div>{paragraphs(x["answer"])}</div></details>' for x in SUPPORT['locales'][locale]['faqs'])
 table = '<thead><tr>' + ''.join(f'<th scope="col">{E(t)}</th>' for t in u['platformHeads']) + '</tr></thead><tbody>' + ''.join('<tr><th scope="row">' + E(r[0]) + '</th>' + ''.join(f'<td>{E(t)}</td>' for t in r[1:]) + '</tr>' for r in u['platformRows']) + '</tbody>'
 body = f'''<main id="main"><section class="hero"><div><p class="eyebrow">{E(u['eyebrow'])}</p><h1>{E(u['hero']).replace(chr(10),'<br>')}</h1><p class="lead">{E(u['lead'])}</p><div class="actions"><a class="button" href="#explore">{E(u['explore'])} <span aria-hidden="true">↓</span></a><a class="button secondary" href="#support">{E(u['help'])}</a></div></div><div><a class="hero-image-link" href="#explore" aria-label="{E(u['explore'])}"><div class="poster"><img src="{hero['large']}" srcset="{hero['small']} {hero['smallWidth']}w, {hero['large']} {hero['largeWidth']}w" sizes="(max-width: 700px) 94vw, 55vw" width="{hero['width']}" height="{hero['height']}" alt="{E(hero['alt'])}" fetchpriority="high"></div></a><p class="hero-caption">{E(caption)}</p></div></section>
<div class="principles">{''.join('<span>'+E(p)+'</span>' for p in u['principles'])}</div>
{film(locale, pre)}
<section id="explore"><div class="section-heading"><div><p class="eyebrow">{E(u['galleryEyebrow'])}</p><h2>{E(u['galleryTitle'])}</h2><p>{E(u['galleryIntro'])}</p></div><div class="device-switch" role="group" aria-label="{E(u['chooseDevice'])}">{buttons}</div></div><p id="gallery-status" class="eyebrow" aria-live="polite">Mac · {E(u['status'])}</p>{fallback_note}<noscript><p class="no-script">{E(u['noScript'])}</p></noscript><div id="gallery" class="gallery" data-device="macos">{cards_html}</div><p class="gallery-note">{E(u['galleryNote'])}</p></section>
<section id="sync" class="sync-section"><div><p class="eyebrow">{E(u['syncEyebrow'])}</p><h2>{E(u['syncTitle']).replace(chr(10),'<br>')}</h2><p>{E(u['syncIntro'])}</p><span class="sync-mark">{E(u['syncMark'])}</span></div><div><div class="sync-card"><h3>{E(u['ordinaryTitle'])}</h3><p>{E(u['ordinaryBody'])}</p></div><div class="sync-card"><h3>{E(u['passwordTitle'])}</h3><p>{E(u['passwordBody'])}</p></div></div></section>
<section class="platforms"><h2>{E(u['platformTitle'])}</h2><table class="platform-table"><caption>{E(u['platformCaption'])}</caption>{table}</table></section>
<section class="support" id="support"><div class="intro"><p class="eyebrow">{E(u['supportEyebrow'])}</p><h2>{E(u['supportTitle'])}</h2><p>{E(u['supportIntro'])}</p><a href="privacy.html">{E(u['privacy'])} ↗</a></div><div class="faq">{faq}</div></section>
<section class="contact" id="contact"><div><h2>{E(u['contactTitle'])}</h2><p>{E(u['contactBody'])}</p><p class="contact-email">{email_link}</p></div><div class="contact-options"><a class="button" href="mailto:{email}">{E(u['emailAction'])}</a><a class="button secondary" href="{SUPPORT['contact']['publicIssueURL']}">{E(u['contactAction'])}</a></div></section></main>
<dialog id="poster-dialog" class="poster-dialog" aria-labelledby="dialog-title"><div class="dialog-bar"><h2 id="dialog-title"></h2><button id="dialog-close" type="button" aria-label="{E(u['close'])}">×</button></div><img id="dialog-image" alt=""></dialog><script id="gallery-data" type="application/json">{serial}</script>'''
 return head + body + footer


def image_report():
 """Device × language poster sets that are not complete, and what the pages show instead."""
 lines = []
 for device in DEVICES:
  for locale in LOCALES:
   if (device['id'], locale) in IMAGE_SETS: continue
   source = image_locale(device['id'], locale)
   effect = 'device hidden' if source is None else f'{source} images with a note'
   lines.append(f"{device['label']} · {locale}: {effect}")
 return lines


def main():
 parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
 parser.add_argument('--sync-copy', nargs='?', const=str(APP_STORE_COPY), metavar='COPY_JSON',
                     help='copy the feature cards from the App Store copy.json (default: %(const)s) before building')
 args = parser.parse_args()
 if args.sync_copy:
  path = Path(args.sync_copy)
  if not path.is_file(): fail(f'{path} not found')
  sync_copy(path)
 load()
 if APP_STORE_COPY.is_file():
  drift = copy_drift(FEATURES, read_json(APP_STORE_COPY))
  if drift:
   print(f'Note: content/features.json differs from {APP_STORE_COPY.name} in {len(drift)} field(s); run with --sync-copy to adopt them:')
   for line in drift: print('  ' + line)
 for locale, meta in LOCALES.items():
  directory = ROOT / meta['dir']; directory.mkdir(exist_ok=True)
  for filename in PAGES:
   (directory / filename).write_text(page(locale, filename))
 print(f'Built {len(LOCALES) * len(PAGES)} static pages: ' + ' / '.join(meta['name'] for meta in LOCALES.values()) + ', home and privacy.')
 missing = image_report()
 if missing:
  print(f'{len(missing)} poster set(s) not yet available:')
  for line in missing: print('  ' + line)


if __name__ == '__main__':
 main()
