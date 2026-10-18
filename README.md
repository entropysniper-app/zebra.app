# Zebra public website

Product and support website for Zebra in four languages, with real Mac, iPhone, iPad and iPhone Duo screenshots and four original comic-style zebra window mascots, assigned by feature.

| Language | Home | Data handling | `hreflang` |
| --- | --- | --- | --- |
| English (also `x-default`) | `index.html` | `privacy.html` | `en` |
| 简体中文 | `zh/index.html` | `zh/privacy.html` | `zh-Hans` |
| 日本語 | `ja/index.html` | `ja/privacy.html` | `ja` |
| Français | `fr/index.html` | `fr/privacy.html` | `fr` |

- Public support: <https://github.com/entropysniper-app/zebra.app/issues>
- Support and privacy email: <entropysniper@gmail.com>

This is a static website. No dependencies, server, account system, analytics scripts or remote fonts are required to serve it, and every page carries the same restrictive Content Security Policy. Each page lists reciprocal `hreflang` alternates for all four languages plus `x-default`. The header language switcher is a native `<details>` disclosure listing the other three languages by their own names; it works without JavaScript, and `site.js` only adds Escape and click-outside dismissal. The main page content and FAQ also remain usable without JavaScript.

The interactive gallery has 10 features × 4 device groups (Mac, iPhone, iPad, iPhone Duo) × 4 languages. Each screenshot has a 720px and a larger WebP variant; the browser chooses a responsive image and the dialog uses the larger version. iPhone Duo uses the landscape inner-display posters, captioned with the iPhone copy that those posters are rendered from.

## GitHub Pages

In this repository, open **Settings → Pages → Build and deployment**:

1. Source: **Deploy from a branch**.
2. Branch: **main**. Folder: **/(root)**.
3. Save and wait for the Pages deployment to finish.

The expected project-site address is <https://entropysniper-app.github.io/zebra.app/>. This repository name does not establish ownership of the `zebra.app` custom domain; no custom domain is configured here. `.nojekyll` serves the static files directly.

Official setup instructions: <https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site>.

## Editing and checking

- Feature cards: `content/features.json`, per platform (`macos`, `iphone`, `ipad`) and App Store locale (`zh-Hans`, `en-US`, `ja`, `fr-FR`). The source of truth is the App Store copy, `AppStoreSubmission/refresh-2026-10-11/copy.json` in the Zebra checkout. `python3 scripts/build.py --sync-copy` copies its cards into `features.json`, printing every changed field, then builds. A plain build only reports any drift from `copy.json` and never changes `features.json`.
- Support FAQ and factual data-handling information: `content/support.json`, one entry per language.
- Page chrome (navigation, hero, sync, platform table, film strings), the language and device lists: `scripts/build.py`. Every language must define every string; the build stops and lists any missing key.
- Presentation and behaviour: `assets/site.css` and `assets/site.js`.

```sh
python3 scripts/build.py
python3 scripts/validate.py
python3 -m http.server 8000
```

Open `http://localhost:8000/`, `/zh/`, `/ja/` or `/fr/`. All links are relative, so the site also works below the `/zebra.app/` path. Rebuild the eight HTML files after changing source copy, templates or images, and commit those outputs with the source changes.

`validate.py` checks every page, local link, anchor and language-switcher target; the reciprocal alternates; the CSP and absence of external resources; that each gallery uses the page's own images or the English fallback with its note; image and video hashes against `asset-manifest.json`; the opaque touch icon; French no-break spacing, the Japanese word ノート, and that no other note app is named. It prints the poster coverage per device and language and lists every missing set. Missing sets are not errors by default; `python3 scripts/validate.py --require-complete` makes them errors for a final delivery.

## Images

### Missing posters

A device × language set is used only when all 10 scenes exist. Until then:

- a language whose own set is missing shows the **English** set for that device, with a visible note under the device switcher (and in the hero caption for Mac); the cards keep their translated copy;
- a device with no complete set in any language (today: iPhone Duo) is **left out** of every page, so no tab or image points to a file that does not exist.

The English fallback keeps every translated page complete and honest about what it shows; hiding the whole gallery would leave the Japanese and French pages without screenshots. A language without its own promo film shows the English film, with a caption saying its text is in English.

### Regenerating

Poster derivatives, the touch icon and `asset-manifest.json` are produced by `scripts/derive_images.js` from the Zebra checkout. It reads the refresh round's `render-manifest.json` (Mac, iPhone and iPad, every rendered language), the Duo round's `render-manifest.json` (iPhone Duo inner display only), and `ZebraMobile/Assets.xcassets/AppIcon.appiconset/AppIcon.png`. Render manifests may be partial or absent; every listed PNG must match its recorded SHA-256. Unchanged posters keep their WebP files, and derivatives whose posters are no longer listed are removed. Only proportional resizing and WebP encoding are applied.

Once new posters are rendered, run from the Zebra repository root:

```sh
# 1. Render and check the posters (see each round's own README).
python3 AppStoreSubmission/refresh-2026-10-11/scripts/render.py
python3 AppStoreSubmission/refresh-2026-10-11/scripts/validate.py --require-complete
swift AppStoreSubmission/duo-2026-10-16/scripts/render.swift
python3 AppStoreSubmission/duo-2026-10-16/scripts/validate.py

# 2. Website derivatives (needs sharp 0.35, installed outside this repository).
npm install --prefix "$TMPDIR/zebra-sharp" sharp@0.35.5
NODE_PATH="$TMPDIR/zebra-sharp/node_modules" node Website/scripts/derive_images.js

# 3. Copy, pages and checks.
python3 Website/scripts/build.py --sync-copy
python3 Website/scripts/validate.py --require-complete
```

Drop `--require-complete` while some sets are still on their way. `derive_images.js` also accepts `--refresh DIR`, `--duo DIR` and `--app-icon PNG`. The older `AppStoreSubmission/refresh-2026-10-11/scripts/web_derivatives.js` knows only the three refresh device groups and a complete render; use `derive_images.js` for this site.

### Icons

`assets/images/icon.png` is the rounded tile with transparent corners, used for the in-page brand mark and the favicon. `assets/images/apple-touch-icon.png` is an opaque, full-bleed 180 × 180 PNG without alpha, derived from the iOS app icon, so a home-screen bookmark shows no white ring; every page references it.

## Content scope

Facts are the same in every language. Semantic search and rich document conversion/export are Mac capabilities, and semantic search currently understands Chinese and English text. Mobile copy describes keyword search, find within notes, attachments and Markdown/package sharing. Note text merges concurrent edits, including notes with a password. A note password is not encryption: password-protected notes are stored and synced as plain text like other notes, and the site must not describe them as encrypted. Sync connects personal devices on the same Apple Account, with iCloud sync off by default for new installations. Other note apps are not named.

All note content in the images is fictional. The synchronization illustration explains the mechanism and is not a recorded sync test. Original App Store poster images were exported separately at their full submission dimensions; the images in this repository are smaller website derivatives. Their provenance and hashes are in `asset-manifest.json`.

The privacy pages are factual product data-handling information. Support and privacy questions can be sent to entropysniper@gmail.com; public reports can also use GitHub Issues. The email address was supplied by the site owner. A formal operator-specific privacy policy still requires the operator's identity; no response-time or retention-period commitment is made here. Share only the information needed to investigate, and do not send passwords or keys.

## Repository relationship

This is an independent Git repository, included in the Zebra app source checkout as the `Website` submodule. Publish website changes to this repository's `main` branch, then update the parent repository's submodule reference. The app source and internal capture evidence are not published here.
