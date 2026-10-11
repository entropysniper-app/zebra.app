'use strict';
(() => {
  const dataElement = document.getElementById('gallery-data');
  if (!dataElement) return;
  const data = JSON.parse(dataElement.textContent);
  const gallery = document.getElementById('gallery');
  const status = document.getElementById('gallery-status');
  const buttons = Array.from(document.querySelectorAll('[data-device-button]'));
  const dialog = document.getElementById('poster-dialog');
  const dialogImage = document.getElementById('dialog-image');
  const dialogTitle = document.getElementById('dialog-title');
  const dialogClose = document.getElementById('dialog-close');
  let sourceButton = null;
  function openPoster(button) {
    sourceButton = button;
    const feature = button.closest('.feature');
    dialogTitle.textContent = feature.querySelector('h3').textContent;
    dialogImage.src = button.dataset.large;
    dialogImage.alt = button.querySelector('img').alt;
    if (typeof dialog.showModal === 'function') {
      dialog.showModal();
      dialogClose.focus();
    } else {
      window.location.assign(button.dataset.large);
    }
  }
  function bindPosters() {
    gallery.querySelectorAll('.feature-image').forEach(button => {
      button.addEventListener('click', () => openPoster(button));
    });
  }
  function closePoster() { dialog.close(); }
  dialogClose.addEventListener('click', closePoster);
  dialog.addEventListener('click', event => {
    if (event.target === dialog) {
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) closePoster();
    }
  });
  dialog.addEventListener('close', () => { if (sourceButton?.isConnected) sourceButton.focus(); });
  function selectDevice(device) {
    if (!Object.hasOwn(data.devices, device)) return;
    const cards = data.devices[device];
    const fragment = document.createDocumentFragment();
    cards.forEach((card, i) => {
      const article = document.createElement('article'); article.className = 'feature';
      const button = document.createElement('button'); button.type = 'button'; button.className = 'feature-image'; button.dataset.large = card.large; button.setAttribute('aria-label', data.viewLabel + ' ' + card.headline);
      const image = document.createElement('img'); image.src = card.small; image.srcset = `${card.small} ${card.smallWidth}w, ${card.large} ${card.largeWidth}w`; image.sizes = device === 'iphone' ? '(max-width: 700px) 45vw, (max-width: 1000px) 30vw, 23vw' : '(max-width: 700px) 94vw, 46vw'; image.width = card.width; image.height = card.height; image.alt = card.alt; image.loading = 'lazy'; image.decoding = 'async';
      const zoom = document.createElement('span'); zoom.className = 'zoom-indicator'; zoom.textContent = '↗'; zoom.setAttribute('aria-hidden','true'); button.append(image,zoom);
      const copy = document.createElement('div'); copy.className = 'feature-copy';
      const top = document.createElement('div'); top.className = 'feature-top';
      const number = document.createElement('span'); number.className = 'feature-index'; number.textContent = String(i+1).padStart(2,'0');
      const heading = document.createElement('h3'); heading.textContent = card.headline;
      const summary = document.createElement('p'); summary.textContent = card.summary;
      top.append(number,heading); copy.append(top,summary); article.append(button,copy); fragment.append(article);
    });
    gallery.replaceChildren(fragment); gallery.dataset.device = device;
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.deviceButton === device)));
    status.textContent = data.deviceLabels[device] + ' · ' + data.statusText;
    bindPosters();
  }
  buttons.forEach(button => button.addEventListener('click', () => selectDevice(button.dataset.deviceButton)));
  bindPosters();
})();
