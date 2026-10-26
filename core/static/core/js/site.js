(() => {
  'use strict';
  const $ = (query, parent = document) => parent.querySelector(query);
  const $$ = (query, parent = document) => [...parent.querySelectorAll(query)];
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const motionButtons = $$('.motion-toggle');
  const isSignedIn = !!$('.logout-form');
  const korean = document.documentElement.lang === 'ko';
  const track = (event, value) => {
    if (!isSignedIn) return;
    fetch('/activity', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': $('meta[name="csrf-token"]').content}, body: JSON.stringify({event, value}), keepalive: true}).catch(() => {});
  };
  let motionPaused = reduced.matches;
  try { motionPaused = motionPaused || localStorage.getItem('reboot-motion') === 'paused'; } catch (_) {}
  function setMotion(paused, save = false) {
    motionPaused = paused;
    document.documentElement.classList.toggle('motion-paused', paused);
    motionButtons.forEach(button => {
      button.setAttribute('aria-pressed', String(paused));
      button.setAttribute('aria-label', korean ? (paused ? '애니메이션 재생' : '애니메이션 일시정지') : (paused ? 'Resume animations' : 'Pause animations'));
      button.textContent = button.closest('.hero-bottom') ? (paused ? '▷' : 'Ⅱ') : korean ? (paused ? '모션 재생 ▷' : '모션 일시정지 Ⅱ') : (paused ? 'Resume motion ▷' : 'Pause motion Ⅱ');
    });
    if (save) {
      try { localStorage.setItem('reboot-motion', paused ? 'paused' : 'playing'); } catch (_) {}
      track('motion_preference', paused ? 'paused' : 'playing');
    }
  }
  setMotion(motionPaused);
  motionButtons.forEach(button => button.addEventListener('click', () => setMotion(!motionPaused, true)));
  reduced.addEventListener('change', e => setMotion(e.matches));

  const menuButton = $('.menu-toggle');
  const mobileNav = $('#mobile-nav');
  function closeMenu() {
    if (!menuButton) return;
    mobileNav.hidden = true;
    menuButton.setAttribute('aria-expanded', 'false');
    menuButton.setAttribute('aria-label', korean ? '메뉴 열기' : 'Open menu');
  }
  menuButton?.addEventListener('click', () => {
    const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!isOpen));
    menuButton.setAttribute('aria-label', korean ? (isOpen ? '메뉴 열기' : '메뉴 닫기') : (isOpen ? 'Open menu' : 'Close menu'));
    mobileNav.hidden = isOpen;
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && mobileNav && !mobileNav.hidden) { closeMenu(); menuButton.focus(); } });
  document.addEventListener('click', e => { if (mobileNav && !mobileNav.hidden && !mobileNav.contains(e.target) && !menuButton.contains(e.target)) closeMenu(); });
  $$('a', mobileNav).forEach(a => a.addEventListener('click', closeMenu));
  window.matchMedia('(min-width: 1001px)').addEventListener('change', e => { if (e.matches) closeMenu(); });
  $$('[data-dismiss]').forEach(button => button.addEventListener('click', () => button.closest('.flash').remove()));

  if ('IntersectionObserver' in window && !reduced.matches) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
    }), {threshold: .08});
    $$('.reveal').forEach(el => { el.classList.add('is-observed'); observer.observe(el); });
  }

  const deck = $('[data-parallax]');
  const art = $('.hero-art');
  art?.addEventListener('pointermove', e => {
    if (motionPaused || reduced.matches || e.pointerType === 'touch') return;
    const bounds = art.getBoundingClientRect();
    deck.style.translate = `${(e.clientX - bounds.left - bounds.width / 2) * .025}px ${(e.clientY - bounds.top - bounds.height / 2) * .025}px`;
  });
  art?.addEventListener('pointerleave', () => { deck.style.translate = '0px 0px'; });
  $$('.hero-swatch').forEach((button, index) => button.addEventListener('click', () => {
    $$('.hero-swatch').forEach(b => { b.classList.toggle('selected', b === button); b.setAttribute('aria-pressed', String(b === button)); });
    const flavor = button.dataset.heroFlavor;
    const img = $('#hero-bottle');
    img.src = button.dataset.src;
    img.alt = `Reboot Original ${flavor.toLowerCase()} drink`;
    $('.card-front').style.background = {Lime: '#cbf498', Lemon: '#f8e88d', Cherry: '#f4abc0'}[flavor];
    $('#hero-flavor-label').textContent = {Lime: 'A LITTLE LIME. A NEW CHAPTER.', Lemon: 'A LITTLE SUNSHINE. ALL YOURS.', Cherry: 'YOUR NEXT CHERRY ON TOP.'}[flavor];
    $('.hero-slide-index').textContent = `0${index + 1} / 03`;
    $('.card-front').href = `/products/drink-original?flavor=${flavor}`;
    track('flavor_selected', `hero:${flavor}`);
  }));

  const carousel = $('.product-carousel');
  function scrollProducts(direction) {
    if (!carousel) return;
    const card = $('.product-card', carousel);
    carousel.scrollBy({left: (card.getBoundingClientRect().width + 22) * direction, behavior: motionPaused || reduced.matches ? 'instant' : 'smooth'});
  }
  $('.carousel-prev')?.addEventListener('click', () => scrollProducts(-1));
  $('.carousel-next')?.addEventListener('click', () => scrollProducts(1));
  carousel?.addEventListener('keydown', e => {
    if (e.target === carousel && ['ArrowLeft', 'ArrowRight'].includes(e.key)) { e.preventDefault(); scrollProducts(e.key === 'ArrowRight' ? 1 : -1); }
  });
  $$('[data-filter]').forEach(button => button.addEventListener('click', () => {
    $$('[data-filter]').forEach(b => { b.classList.toggle('active', b === button); b.setAttribute('aria-pressed', String(b === button)); });
    const filter = button.dataset.filter;
    $$('.product-grid .product-card').forEach(card => { card.hidden = filter !== 'all' && card.dataset.format !== filter && card.dataset.edition !== filter; });
    track('collection_filtered', filter);
  }));

  const productForm = $('.product-form');
  function changeFlavor(input, sendEvent = true) {
    const img = $('#detail-image');
    img.src = input.dataset.image;
    // The backdrop follows the flavor, so a cherry bottle never sits on a lime card.
    const visual = img.closest('.detail-visual');
    visual.classList.remove('tone-lime', 'tone-lemon', 'tone-cherry');
    visual.classList.add(`tone-${input.value.toLowerCase()}`);
    img.alt = `${$('.detail-copy h1').textContent.trim()} in ${input.value}`;
    if (sendEvent) track('flavor_selected', `${location.pathname.split('/').pop()}:${input.value}`);
  }
  $$('input[name="flavor"]', productForm || document).forEach(input => input.addEventListener('change', () => changeFlavor(input)));
  if (productForm) {
    const flavor = new URLSearchParams(location.search).get('flavor');
    const input = $$('input[name="flavor"]', productForm).find(i => i.value === flavor);
    if (input) { input.checked = true; changeFlavor(input, false); }
    $$('input[name="sku"]', productForm).forEach(input => input.addEventListener('change', () => { $('#detail-price').textContent = new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(Number(input.dataset.price)); }));
  }
  $$('[data-step]').forEach(button => button.addEventListener('click', () => {
    const input = $('input[type="number"]', button.parentElement);
    input.value = String(Math.max(Number(input.min), Math.min(Number(input.max), (Number(input.value) || 1) + Number(button.dataset.step))));
    input.dispatchEvent(new Event('change', {bubbles: true}));
  }));
  $$('[data-remove-item]').forEach(button => { button.name = 'action'; button.value = 'remove'; });
  $$('form').forEach(form => form.addEventListener('submit', () => {
    const button = $('[data-submit-once]', form);
    if (button) { button.disabled = true; button.textContent = korean ? '저장 중…' : 'Saving…'; }
  }));
  window.addEventListener('pageshow', () => $$('[data-submit-once]').forEach(button => { if (button.disabled) location.reload(); }));

  const quiz = $('.vibe-form');
  if (quiz) {
    const questions = $$('.vibe-question', quiz);
    const next = $('.quiz-next', quiz), back = $('.quiz-back', quiz), submit = $('.quiz-submit', quiz);
    let step = 0;
    quiz.noValidate = true;
    function showStep() {
      questions.forEach((q, i) => { q.hidden = i !== step; });
      back.hidden = step === 0;
      next.hidden = step === questions.length - 1;
      submit.hidden = step !== questions.length - 1;
      $$('.quiz-progress span', quiz).forEach((bar, i) => bar.classList.toggle('complete', i <= step));
      const first = $('input', questions[step]);
      first?.focus({preventScroll: true});
    }
    function validStep() {
      if ($('input:checked', questions[step])) return true;
      $('input', questions[step]).reportValidity();
      return false;
    }
    next.addEventListener('click', () => { if (validStep()) { track('quiz_step', String(step + 1)); step++; showStep(); } });
    back.addEventListener('click', () => { step = Math.max(0, step - 1); showStep(); });
    quiz.addEventListener('submit', e => {
      if (!validStep()) { e.preventDefault(); return; }
      if (step !== questions.length - 1) { e.preventDefault(); step++; showStep(); }
    });
    showStep();
  }
})();
