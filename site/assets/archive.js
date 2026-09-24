(() => {
  const archive = document.querySelector('.archive');
  if (!archive) return;

  const search = archive.querySelector('#story-search');
  const cards = [...archive.querySelectorAll('.story-card')];
  const buttons = [...archive.querySelectorAll('[data-filter]')];
  const count = archive.querySelector('#archive-count');
  const empty = archive.querySelector('#archive-empty');
  let active = 'all';
  archive.classList.add('is-ready');

  function update() {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const card of cards) {
      const matches = (active === 'all' || card.dataset.kind === active)
        && (!query || card.dataset.search.includes(query));
      card.hidden = !matches;
      if (matches) visible += 1;
    }
    count.textContent = `Showing ${visible} ${visible === 1 ? 'story' : 'stories'}`;
    empty.hidden = visible !== 0;
  }

  search.addEventListener('input', update);
  for (const button of buttons) {
    button.addEventListener('click', () => {
      active = button.dataset.filter;
      for (const choice of buttons) choice.setAttribute('aria-pressed', String(choice === button));
      update();
    });
  }
})();
