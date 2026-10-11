# Zebra public website

Bilingual product and support website for Zebra, with real Mac, iPhone and iPad screenshots and an original zebra window mascot.

- English: `index.html`
- 简体中文：`zh/index.html`
- Data handling: `privacy.html` and `zh/privacy.html`
- Public support: <https://github.com/entropysniper-app/zebra.app/issues>

This is a static website. No dependencies, server, account system, analytics scripts or remote fonts are required to serve it. The interactive gallery has 8 features × 3 devices × 2 languages. Each screenshot has a 720px and a larger WebP variant. The browser chooses a responsive image; the dialog uses the larger version. The main page content and FAQ remain usable without JavaScript.

## GitHub Pages

In this repository, open **Settings → Pages → Build and deployment**:

1. Source: **Deploy from a branch**.
2. Branch: **main**. Folder: **/(root)**.
3. Save and wait for the Pages deployment to finish.

The expected project-site address is <https://entropysniper-app.github.io/zebra.app/>. This repository name does not establish ownership of the `zebra.app` custom domain; no custom domain is configured here. `.nojekyll` serves the static files directly.

Official setup instructions: <https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site>.

## Editing and checking

Reviewed feature copy is in `content/features.json`. Support and factual data-handling information are in `content/support.json`. Shared layout text and templates are in `scripts/build.py`; presentation and gallery behavior are in `assets/site.css` and `assets/site.js`.

```sh
python3 scripts/build.py
python3 scripts/validate.py
python3 -m http.server 8000
```

Open `http://localhost:8000/` or `http://localhost:8000/zh/`. The site also works when hosted below the `/zebra.app/` path. Rebuild the four HTML files after changing source copy or templates, and commit those outputs with the source changes.

## Content scope

Semantic search and rich document conversion/export are Mac capabilities. Mobile copy describes keyword search, find within notes, attachments and Markdown/package sharing. Ordinary note text merges concurrent edits; encrypted notes retain concurrent encrypted versions. Sync connects personal devices on the same Apple Account, with iCloud sync off by default for new installations.

All note content in the images is fictional. The synchronization illustration explains the mechanism and is not a recorded sync test. Original App Store poster images were exported separately at their full submission dimensions; the images in this repository are smaller website derivatives. Their provenance and hashes are in `asset-manifest.json`.

The privacy pages are factual product data-handling information. A formal operator-specific privacy policy and private support email have not been supplied; this site does not invent them or make a response-time commitment. Public reports use GitHub Issues. Do not attach private notes, passwords, keys or complete libraries.

## Repository relationship

This is an independent Git repository, included in the Zebra app source checkout as the `Website` submodule. Publish website changes to this repository's `main` branch, then update the parent repository's submodule reference. The app source and internal capture evidence are not published here.
