(() => {
  'use strict';
  const root = document.querySelector('[data-flavor-carousel]');
  if (!root) return;
  const $ = query => root.querySelector(query);
  const $$ = query => [...root.querySelectorAll(query)];
  const viewport = $('.flavor-viewport');
  const items = $$('.flavor-item');
  const panels = $$('.flavor-panel');
  const thumbs = $$('.flavor-thumb');
  const more = $('[data-flavor-more]');
  const N = items.length;
  const STEP = 360 / N;
  const DURATION = 900;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mod = (n, m) => ((n % m) + m) % m;
  // power3.inOut
  const ease = t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const instant = () => reduced.matches || document.documentElement.classList.contains('motion-paused');

  let radius = 400;
  let pos = 0;            // fractional position currently drawn (unbounded, so the loop never jumps)
  let target = 0;         // integer position we are heading to
  let tween = null;       // {from, to, start}
  let shownPanel = 0;
  let drag = null;

  function measure() {
    const width = viewport.clientWidth;
    radius = Math.min(width * (width < 760 ? .62 : .36), 600);
    render();
  }

  // swing: a small rotateZ while the ring moves, so products sway like real objects instead of turning flat cards.
  function render(swing = 0) {
    items.forEach((item, i) => {
      let rel = mod(i - pos + N / 2, N) - N / 2;  // -N/2 .. N/2, 0 = front and centre
      const dist = Math.abs(rel);
      const angle = rel * STEP;
      const scale = 1 + .22 * Math.max(0, 1 - dist);
      // Place on the ring (rotateY + translateZ), then face the viewer again: the photo itself shows the turn
      // (real three-quarter render at the sides, front render in the middle), so the image plane never shows its flatness.
      item.style.transform = `translateZ(${-radius}px) rotateY(${angle}deg) translateZ(${radius}px) rotateY(${-angle}deg) rotate(${swing * Math.max(.4, 1 - dist * .3)}deg) scale(${scale})`;
      item.style.opacity = String(Math.max(0, 1 - dist * .32));
      item.style.zIndex = String(100 - Math.round(dist * 10));
      item.style.visibility = dist > 3.4 ? 'hidden' : 'visible';
      // Swap to the front-facing photo only in the last stretch of the turn, so the two views never ghost.
      item.style.setProperty('--center', String(Math.max(0, Math.min(1, 1 - dist * 3.5))));
      item.classList.toggle('is-left', rel < 0);
      item.classList.toggle('is-center', dist < .5);
    });
  }

  function select(index) {
    const color = items[index].dataset.color;
    root.style.setProperty('--stage-bg', color);
    more.href = items[index].dataset.url;
    thumbs.forEach((thumb, i) => { thumb.classList.toggle('is-active', i === index); thumb.setAttribute('aria-pressed', String(i === index)); });
    items.forEach((item, i) => item.setAttribute('aria-hidden', String(i !== index)));
  }

  function showPanel(index) {
    if (shownPanel === index && panels[index].classList.contains('is-active')) return;
    panels.forEach((panel, i) => { panel.classList.toggle('is-active', i === index); panel.hidden = i !== index; });
    shownPanel = index;
  }

  function hidePanels() {
    panels.forEach(panel => panel.classList.remove('is-active'));
  }

  function goTo(newTarget) {
    target = newTarget;
    const index = mod(target, N);
    select(index);
    if (instant()) {
      tween = null; pos = target; render(); showPanel(index);
      return;
    }
    hidePanels();
    // Start from wherever we are drawn now, so rapid input re-aims smoothly instead of stacking.
    const running = tween !== null;
    tween = {from: pos, to: target, start: performance.now()};
    if (!running) requestAnimationFrame(frame);
  }

  function frame(now) {
    if (!tween) return;
    const t = Math.min(1, (now - tween.start) / DURATION);
    const before = pos;
    pos = tween.from + (tween.to - tween.from) * ease(t);
    render(Math.max(-9, Math.min(9, (before - pos) * 220)));
    if (t >= .7) showPanel(mod(tween.to, N));
    if (t < 1) requestAnimationFrame(frame);
    else { pos = tween.to; tween = null; render(); }
  }

  const step = direction => goTo(target + direction);
  const nearest = index => target + (mod(index - target + N / 2, N) - N / 2);

  $('[data-flavor-prev]').addEventListener('click', () => step(-1));
  $('[data-flavor-next]').addEventListener('click', () => step(1));
  thumbs.forEach(thumb => thumb.addEventListener('click', () => goTo(nearest(Number(thumb.dataset.thumb)))));
  viewport.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
    if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
  });

  // Mouse drag and touch swipe: the ring follows the pointer, then snaps to the nearest product.
  viewport.addEventListener('pointerdown', e => {
    if (e.button !== 0 || e.target.closest('a, button')) return;
    drag = {x: e.clientX, startPos: pos, moved: false, id: e.pointerId};
    tween = null;
  });
  viewport.addEventListener('pointermove', e => {
    if (!drag || e.pointerId !== drag.id) return;
    const dx = e.clientX - drag.x;
    if (!drag.moved && Math.abs(dx) < 6) return;
    if (!drag.moved) { drag.moved = true; viewport.setPointerCapture(e.pointerId); viewport.classList.add('is-dragging'); hidePanels(); }
    const before = pos;
    pos = drag.startPos - dx / (radius * .55);
    render(Math.max(-9, Math.min(9, (before - pos) * 140)));
  });
  function endDrag(e) {
    if (!drag || e.pointerId !== drag.id) return;
    const {moved, x} = drag;
    drag = null;
    viewport.classList.remove('is-dragging');
    if (moved) {
      const dx = e.clientX - x;
      // A quick flick always advances at least one product.
      let next = Math.round(pos);
      if (next === Math.round(target) && Math.abs(dx) > 40) next = target + (dx < 0 ? 1 : -1);
      goTo(next);
    } else {
      // Plain click/tap: open the front product, or bring a side product to the front.
      const item = e.target.closest('.flavor-item');
      if (!item) { goTo(target); return; }
      const index = Number(item.dataset.index);
      if (index === mod(target, N) && !tween) window.location.href = item.dataset.url;
      else goTo(nearest(index));
    }
  }
  viewport.addEventListener('pointerup', endDrag);
  viewport.addEventListener('pointercancel', e => { if (drag) { drag = null; viewport.classList.remove('is-dragging'); goTo(Math.round(pos)); } });

  window.addEventListener('resize', measure);
  root.classList.add('is-ready');
  measure();
  select(0);
})();
