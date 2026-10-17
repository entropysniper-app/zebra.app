#!/usr/bin/env node
// Regenerates the website's WebP poster derivatives, the opaque apple-touch-icon and
// asset-manifest.json from the frozen App Store posters in the Zebra checkout:
//
//   • refresh round  AppStoreSubmission/refresh-2026-10-11/render-manifest.json
//                    (Mac, iPhone and iPad posters, every rendered language)
//   • Duo round      AppStoreSubmission/duo-2026-10-16/render-manifest.json
//                    (iPhone Duo inner-display posters, landscape; outer posters are not used)
//   • touch icon     ZebraMobile/Assets.xcassets/AppIcon.appiconset/AppIcon.png
//
// Posters are taken as they appear: a render manifest may be partial (some languages or
// scenes not rendered yet) or absent. Every listed PNG must still match its recorded
// SHA-256, so a poster that changed after rendering stops the run. Only proportional
// resizing and WebP encoding are applied. Unchanged posters keep their existing WebP files.
// The site build shows a device × language set only when all its scenes are present.
//
// Needs sharp 0.35 outside this repository, e.g.
//   npm install --prefix "$TMPDIR/zebra-sharp" sharp@0.35.5
//   NODE_PATH="$TMPDIR/zebra-sharp/node_modules" node scripts/derive_images.js [--refresh DIR] [--duo DIR] [--app-icon PNG]
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const sharp = require('sharp');

const SITE = path.resolve(__dirname, '..');
const REPO = path.resolve(SITE, '..');
const option = (name, fallback) => {
  const index = process.argv.indexOf(name);
  return index > 0 && process.argv[index + 1] ? path.resolve(process.argv[index + 1]) : fallback;
};
const REFRESH = option('--refresh', path.join(REPO, 'AppStoreSubmission/refresh-2026-10-11'));
const DUO = option('--duo', path.join(REPO, 'AppStoreSubmission/duo-2026-10-16'));
const APP_ICON = option('--app-icon', path.join(REPO, 'ZebraMobile/Assets.xcassets/AppIcon.appiconset/AppIcon.png'));
// Device groups this script owns under assets/images/<platform>/<locale>/.
const PLATFORMS = ['macos', 'iphone', 'ipad', 'iphone-duo'];
const WIDTHS = { small: 720, large: 1440 };
const WEBP = { quality: 86, effort: 6, smartSubsample: true };
const TOUCH_ICON = { path: 'assets/images/apple-touch-icon.png', size: 180 };

const sha256 = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const repoPath = (absolute) => path.relative(REPO, absolute).split(path.sep).join('/');
const readJSON = (file) => JSON.parse(fs.readFileSync(file));

async function derive(png, width, destination) {
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  // sharp drops source metadata unless asked to keep it.
  const info = await sharp(png).resize({ width, withoutEnlargement: true }).toColorspace('srgb').webp(WEBP).toFile(destination);
  const bytes = fs.readFileSync(destination);
  return { width: info.width, height: info.height, bytes: bytes.length, sha256: sha256(bytes) };
}

function verifiedPNG(round, relative, expected) {
  const file = path.join(round, relative);
  if (!fs.existsSync(file)) throw new Error(`${repoPath(file)} is listed in its render manifest but missing`);
  const png = fs.readFileSync(file);
  if (sha256(png) !== expected) throw new Error(`${repoPath(file)} differs from its render manifest; re-render before deriving`);
  return png;
}

// Refresh-round posters: every rendered item, whether or not the whole render is complete.
function refreshPosters() {
  const manifestFile = path.join(REFRESH, 'render-manifest.json');
  if (!fs.existsSync(manifestFile)) return { posters: [], source: null };
  const bytes = fs.readFileSync(manifestFile);
  const render = JSON.parse(bytes);
  if (render.proof || render.layoutOnly) throw new Error(`${repoPath(manifestFile)} describes development proofs, not final posters`);
  const posters = render.items.filter((item) => item.state === 'rendered-from-raw').map((item) => ({
    png: verifiedPNG(REFRESH, item.png, item.pngSHA256),
    entry: {
      platform: item.platform,
      locale: item.locale,
      scene: item.scene,
      slug: path.basename(item.png, '.png'),
      source: { repository: 'zebra', path: repoPath(path.join(REFRESH, item.png)), sha256: item.pngSHA256, width: item.size[0], height: item.size[1] },
      copySHA256: item.copySHA256,
      captureSources: item.sources.map((source) => ({ path: repoPath(path.join(REFRESH, source.source)), sha256: source.sourceSHA256, appThemeRawValue: source.appThemeRawValue })),
      decorativeAssets: item.decorativeAssets.map((asset) => ({
        id: asset.id, variantID: asset.variantID, path: repoPath(path.join(REFRESH, asset.source)), sha256: asset.sha256, role: asset.role,
      })),
    },
  }));
  return { posters, source: { repository: 'zebra', path: repoPath(manifestFile), sha256: sha256(bytes), complete: Boolean(render.complete) } };
}

// Duo-round posters: inner-display (landscape) renders only.
function duoPosters() {
  const manifestFile = path.join(DUO, 'render-manifest.json');
  if (!fs.existsSync(manifestFile)) return { posters: [], source: null };
  const bytes = fs.readFileSync(manifestFile);
  const render = JSON.parse(bytes);
  if (render.layoutOnly) throw new Error(`${repoPath(manifestFile)} describes layout proofs, not final posters`);
  const captures = fs.existsSync(path.join(DUO, 'capture-manifest.json')) ? readJSON(path.join(DUO, 'capture-manifest.json')).captures : [];
  const theme = (relative) => (captures.find((capture) => capture.path === relative) || {}).appThemeRawValue;
  const posters = render.renders.filter((item) => item.variant === 'inner' && !item.layoutOnly).map((item) => ({
    png: verifiedPNG(DUO, item.output, item.outputSHA256),
    entry: {
      platform: 'iphone-duo',
      display: 'inner',
      locale: item.locale,
      scene: item.scene,
      slug: path.basename(item.output, '.png'),
      source: { repository: 'zebra', path: repoPath(path.join(DUO, item.output)), sha256: item.outputSHA256, width: item.dimensions[0], height: item.dimensions[1] },
      copySHA256: render.copySHA256,
      captureSources: [{ path: repoPath(path.join(DUO, item.source)), sha256: item.sourceSHA256, appThemeRawValue: theme(item.source) }],
      // The Duo renderer reads mascots from the refresh round's brand folder.
      decorativeAssets: [{
        id: 'zebra-window-mascot', variantID: path.basename(item.mascot, '.png'), path: repoPath(path.join(REFRESH, item.mascot)),
        sha256: item.mascotSHA256, role: 'decorative brand asset; not captured application UI',
      }],
    },
  }));
  return { posters, source: { repository: 'zebra', path: repoPath(manifestFile), sha256: sha256(bytes), complete: render.missing.length === 0 && render.failures.length === 0 } };
}

// A full-bleed, opaque home-screen icon: iOS rounds it, so there is no transparent ring.
async function touchIcon(previous) {
  const source = fs.readFileSync(APP_ICON);
  const destination = path.join(SITE, TOUCH_ICON.path);
  const old = previous.find((asset) => asset.id === 'apple-touch-icon');
  if (old && old.source.sha256 === sha256(source) && fs.existsSync(destination) && sha256(fs.readFileSync(destination)) === old.sha256) return old;
  const meta = await sharp(source).metadata();
  if (meta.width !== meta.height) throw new Error(`${repoPath(APP_ICON)} is not square`);
  await sharp(source).resize(TOUCH_ICON.size, TOUCH_ICON.size, { kernel: 'lanczos3' }).removeAlpha().toColorspace('srgb')
    .png({ compressionLevel: 9, adaptiveFiltering: true }).toFile(destination);
  const bytes = fs.readFileSync(destination);
  return {
    id: 'apple-touch-icon',
    source: { repository: 'zebra', path: repoPath(APP_ICON), sha256: sha256(source) },
    path: TOUCH_ICON.path, width: TOUCH_ICON.size, height: TOUCH_ICON.size, hasAlpha: false, bytes: bytes.length, sha256: sha256(bytes),
    transformation: `Proportional Lanczos resize of the opaque, full-bleed 1024-pixel iOS AppIcon to ${TOUCH_ICON.size} pixels; alpha channel removed; lossless PNG; source metadata stripped.`,
  };
}

function removeOrphans(keep) {
  const removed = [];
  const walk = (dir) => {
    if (!fs.existsSync(dir)) return;
    for (const name of fs.readdirSync(dir)) {
      const file = path.join(dir, name);
      if (fs.statSync(file).isDirectory()) { walk(file); if (fs.readdirSync(file).length === 0) fs.rmdirSync(file); }
      else if (name.endsWith('.webp') && !keep.has(file)) { fs.unlinkSync(file); removed.push(path.relative(SITE, file)); }
    }
  };
  for (const platform of PLATFORMS) {
    const dir = path.join(SITE, 'assets/images', platform);
    walk(dir);
    if (fs.existsSync(dir) && fs.readdirSync(dir).length === 0) fs.rmdirSync(dir);
  }
  return removed;
}

async function main() {
  const manifestPath = path.join(SITE, 'asset-manifest.json');
  const previous = readJSON(manifestPath);
  const generator = { ...previous.generator, version: sharp.versions.sharp, quality: WEBP.quality, effort: WEBP.effort, smartSubsample: WEBP.smartSubsample };
  const sameSettings = JSON.stringify(previous.generator) === JSON.stringify(generator);
  const reusable = new Map(previous.posters.map((poster) => [`${poster.platform}/${poster.locale}/${poster.scene}`, poster]));
  const refresh = refreshPosters();
  const duo = duoPosters();
  const keep = new Set();
  const totals = { original: 0, small: 0, large: 0 };
  const posters = [];
  let encoded = 0;
  for (const { png, entry } of [...refresh.posters, ...duo.posters]) {
    const key = `${entry.platform}/${entry.locale}/${entry.scene}`;
    if (posters.some((poster) => `${poster.platform}/${poster.locale}/${poster.scene}` === key)) throw new Error(`Two posters for ${key}`);
    const old = reusable.get(key);
    const variants = {};
    for (const [name, target] of Object.entries(WIDTHS)) {
      const relative = `assets/images/${entry.platform}/${entry.locale}/${entry.slug}-${name}.webp`;
      const destination = path.join(SITE, relative);
      const prior = old && old.variants[name];
      const unchanged = sameSettings && old && old.source.sha256 === entry.source.sha256 && prior.path === relative
        && fs.existsSync(destination) && sha256(fs.readFileSync(destination)) === prior.sha256;
      if (unchanged) variants[name] = prior;
      else { variants[name] = { path: relative, ...(await derive(png, Math.min(target, entry.source.width), destination)) }; encoded += 1; }
      keep.add(destination);
      totals[name] += variants[name].bytes;
    }
    entry.source.bytes = png.length;
    totals.original += png.length;
    posters.push({ ...entry, variants });
  }
  const removed = removeOrphans(keep);
  const branding = [...previous.branding.filter((asset) => asset.id !== 'apple-touch-icon'), await touchIcon(previous.branding)];
  const brandBytes = branding.reduce((sum, asset) => sum + asset.bytes, 0);
  const coverage = {};
  for (const poster of posters) {
    coverage[poster.platform] = coverage[poster.platform] || {};
    coverage[poster.platform][poster.locale] = (coverage[poster.platform][poster.locale] || 0) + 1;
  }
  const platforms = Object.keys(coverage);
  const locales = [...new Set(posters.map((poster) => poster.locale))];
  const { sourceRenderManifest, locales: staleLocales, ...rest } = previous; // superseded by sourceRenderManifests and the posters themselves
  const manifest = {
    ...rest,
    schemaVersion: 3,
    generatedAt: new Date().toISOString(),
    description: `Web derivatives of ${posters.length} final Zebra App Store posters across ${platforms.length} device groups and ${locales.length} languages (${locales.join(', ')}). Only proportional resizing and WebP encoding were applied to the frozen posters. iPhone Duo uses the inner-display posters.`,
    generator,
    sourceRenderManifests: [refresh.source, duo.source].filter(Boolean),
    branding,
    posters,
    summary: {
      posterCount: posters.length,
      webpCount: posters.length * Object.keys(WIDTHS).length,
      brandPngCount: branding.length,
      originalPosterBytes: totals.original,
      smallWebpBytes: totals.small,
      largeWebpBytes: totals.large,
      brandPngBytes: brandBytes,
      totalImageBytes: totals.small + totals.large + brandBytes,
      postersByDeviceAndLanguage: coverage,
    },
  };
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  console.log(JSON.stringify({
    refreshPosters: refresh.posters.length, duoInnerPosters: duo.posters.length,
    duoRenderManifest: duo.source ? 'found' : 'not rendered yet', webpEncoded: encoded, webpReused: posters.length * 2 - encoded,
    webpRemoved: removed.length, coverage,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
