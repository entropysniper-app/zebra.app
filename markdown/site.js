document.querySelectorAll('[data-gallery]').forEach((gallery) => {
  const tabs = Array.from(gallery.querySelectorAll('[role="tab"]'));
  const panels = Array.from(gallery.querySelectorAll('[role="tabpanel"]'));
  const select = (index, focus = false) => {
    tabs.forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
      panels[i].hidden = i !== index;
    });
    if (focus) tabs[index].focus();
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(index));
    tab.addEventListener('keydown', (event) => {
      const next = { ArrowRight: (index + 1) % tabs.length,
        ArrowLeft: (index + tabs.length - 1) % tabs.length,
        Home: 0, End: tabs.length - 1 }[event.key];
      if (next !== undefined) { event.preventDefault(); select(next, true); }
    });
  });
  gallery.classList.add('enhanced');
  select(1);
});

const language = document.querySelector('.language');
document.addEventListener('click', (event) => {
  if (language && !language.contains(event.target)) language.open = false;
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && language?.open) {
    language.open = false;
    language.querySelector('summary').focus();
  }
});

const revealAnchor = () => {
  if (location.hash === '#restore-purchases') {
    const restore = document.getElementById('restore-purchases');
    restore.open = true;
    restore.scrollIntoView({ block: 'start' });
  }
};
window.addEventListener('hashchange', revealAnchor);
revealAnchor();
