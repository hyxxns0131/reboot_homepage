(() => {
  'use strict';
  const root = document.querySelector('[data-game]');
  if (!root) return;
  const $ = query => root.querySelector(query);
  const $$ = query => [...root.querySelectorAll(query)];
  const canvas = $('canvas');
  const ctx = canvas.getContext('2d');
  const W = 960, H = 600, ROUND = 60;
  const FLAVORS = {Lime: '#9bdc44', Lemon: '#efd660', Cherry: '#e781a3'};
  const korean = document.documentElement.lang === 'ko';
  const signedIn = !!document.querySelector('.logout-form');
  const mark = new Image();
  mark.src = root.dataset.mark;

  const hud = {score: $('[data-score]'), combo: $('[data-combo]'), time: $('[data-time]'), lives: $('[data-lives]'), best: $('[data-best]')};
  const pauseButton = $('[data-pause]');
  let best = 0;
  try { best = Number(localStorage.getItem('reboot-catch-best')) || 0; } catch (_) {}
  hud.best.textContent = best;

  const player = {x: W / 2, w: 150, h: 84, target: W / 2};
  let state = 'start', items = [], bursts = [], score = 0, combo = 0, lives = 3, timeLeft = ROUND, spawnIn = 0, last = 0, caught = {};

  function show(screen) {
    $$('[data-screen]').forEach(el => { el.hidden = el.dataset.screen !== screen; });
  }

  function updateHud() {
    hud.score.textContent = score;
    hud.combo.textContent = `×${multiplier()}`;
    hud.time.textContent = Math.ceil(timeLeft);
    hud.lives.textContent = '●'.repeat(3 - lives) + '○'.repeat(lives);
  }

  const multiplier = () => 1 + Math.floor(combo / 5);

  function start() {
    items = []; bursts = []; score = 0; combo = 0; lives = 3; timeLeft = ROUND; spawnIn = 0; caught = {Lime: 0, Lemon: 0, Cherry: 0};
    player.x = player.target = W / 2;
    state = 'playing';
    show(null);
    pauseButton.disabled = false;
    updateHud();
    last = performance.now();
    canvas.focus({preventScroll: true});
    requestAnimationFrame(loop);
  }

  function pause(paused) {
    if (paused && state === 'playing') { state = 'paused'; show('paused'); }
    else if (!paused && state === 'paused') { state = 'playing'; show(null); last = performance.now(); requestAnimationFrame(loop); }
    pauseButton.textContent = state === 'paused' ? (korean ? '계속하기 ▷' : 'Resume ▷') : (korean ? '일시정지 Ⅱ' : 'Pause Ⅱ');
  }

  function finish() {
    state = 'over';
    pauseButton.disabled = true;
    const top = Object.entries(caught).sort((a, b) => b[1] - a[1])[0][0];
    const isBest = score > best;
    if (isBest) {
      best = score;
      hud.best.textContent = best;
      try { localStorage.setItem('reboot-catch-best', String(best)); } catch (_) {}
    }
    $('[data-final]').textContent = score;
    $('.game-new-best').hidden = !isBest || score === 0;
    $('[data-top-flavor]').textContent = korean ? {Lime: '라임', Lemon: '레몬', Cherry: '체리'}[top] : top;
    $('[data-flavor-link]').href = `${root.dataset.productUrl}?flavor=${top}`;
    show('over');
    if (signedIn) {
      fetch('/activity', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content}, body: JSON.stringify({event: 'game_score', value: `${score}:${top}`}), keepalive: true}).catch(() => {});
    }
  }

  function spawn() {
    const elapsed = ROUND - timeLeft;
    const clock = Math.random() < Math.min(.12 + elapsed * .004, .32);
    const flavor = Object.keys(FLAVORS)[Math.floor(Math.random() * 3)];
    items.push({x: 40 + Math.random() * (W - 80), y: -30, r: clock ? 24 : 22, vy: 170 + elapsed * 4 + Math.random() * 90, spin: Math.random() * 6, clock, flavor});
    spawnIn = Math.max(.32, .85 - elapsed * .009) * (.7 + Math.random() * .6);
  }

  function step(dt) {
    timeLeft -= dt;
    if (timeLeft <= 0) { timeLeft = 0; updateHud(); finish(); return; }
    spawnIn -= dt;
    if (spawnIn <= 0) spawn();
    player.x += (player.target - player.x) * Math.min(1, dt * 14);
    const top = H - 26 - player.h;
    for (const item of items) {
      item.y += item.vy * dt;
      item.spin += dt * 2;
      if (!item.done && item.y + item.r > top + 18 && item.y - item.r < H - 26 && Math.abs(item.x - player.x) < player.w / 2 + item.r * .4) {
        item.done = true;
        if (item.clock) {
          lives -= 1; combo = 0;
          bursts.push({x: item.x, y: item.y, t: 0, text: 'SNOOZE', color: '#ff4d6d'});
          if (lives <= 0) { updateHud(); finish(); return; }
        } else {
          combo += 1;
          const points = 10 * multiplier();
          score += points;
          caught[item.flavor] += 1;
          bursts.push({x: item.x, y: item.y, t: 0, text: `+${points}`, color: FLAVORS[item.flavor]});
        }
      } else if (!item.done && item.y - item.r > H) {
        item.done = true;
        if (!item.clock) combo = 0;
      }
    }
    items = items.filter(item => !item.done);
    bursts.forEach(b => { b.t += dt; });
    bursts = bursts.filter(b => b.t < .7);
    updateHud();
  }

  function drawFruit(item) {
    ctx.save();
    ctx.translate(item.x, item.y);
    ctx.fillStyle = FLAVORS[item.flavor];
    ctx.beginPath(); ctx.arc(0, 0, item.r, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = 'rgba(16,16,16,.35)'; ctx.lineWidth = 2;
    for (let i = 0; i < 6; i++) {
      const a = item.spin + i * Math.PI / 3;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * item.r * .78, Math.sin(a) * item.r * .78); ctx.stroke();
    }
    ctx.fillStyle = 'rgba(255,255,255,.55)';
    ctx.beginPath(); ctx.ellipse(-item.r * .35, -item.r * .45, item.r * .28, item.r * .14, -.6, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

  function drawClock(item) {
    ctx.save();
    ctx.translate(item.x, item.y);
    ctx.rotate(Math.sin(item.spin * 3) * .25);
    ctx.fillStyle = '#2c2d29'; ctx.strokeStyle = '#ff4d6d'; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.arc(0, 0, item.r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.arc(-item.r * .7, -item.r * .85, 8, 0, Math.PI * 2); ctx.arc(item.r * .7, -item.r * .85, 8, 0, Math.PI * 2); ctx.fillStyle = '#ff4d6d'; ctx.fill();
    ctx.strokeStyle = '#f5f4ee'; ctx.lineWidth = 3; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -item.r * .6); ctx.moveTo(0, 0); ctx.lineTo(item.r * .45, item.r * .2); ctx.stroke();
    ctx.fillStyle = '#f5f4ee'; ctx.font = 'bold 13px Arial, sans-serif'; ctx.fillText('z', item.r * .8, -item.r * 1.1);
    ctx.restore();
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(245,244,238,.06)'; ctx.lineWidth = 1;
    for (let x = 60; x < W; x += 60) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    ctx.fillStyle = '#1d1f1a'; ctx.fillRect(0, H - 26, W, 26);
    ctx.fillStyle = '#61e728'; ctx.fillRect(0, H - 26, W * (timeLeft / ROUND), 3);
    items.forEach(item => (item.clock ? drawClock : drawFruit)(item));
    const px = player.x - player.w / 2, py = H - 26 - player.h;
    ctx.save();
    ctx.shadowColor = 'rgba(97,231,40,.55)'; ctx.shadowBlur = 26;
    if (mark.complete && mark.naturalWidth) ctx.drawImage(mark, px, py, player.w, player.h);
    else { ctx.fillStyle = '#61e728'; ctx.fillRect(px, py + player.h / 2, player.w, player.h / 2); }
    ctx.restore();
    ctx.textAlign = 'center'; ctx.font = 'bold 24px Arial, sans-serif';
    bursts.forEach(b => { ctx.globalAlpha = 1 - b.t / .7; ctx.fillStyle = b.color; ctx.fillText(b.text, b.x, b.y - b.t * 70); });
    ctx.globalAlpha = 1; ctx.textAlign = 'start';
  }

  function loop(now) {
    if (state !== 'playing') return;
    const dt = Math.min((now - last) / 1000, .05);
    last = now;
    step(dt);
    draw();
    if (state === 'playing') requestAnimationFrame(loop);
  }

  function resize() {
    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width * ratio);
    canvas.height = Math.round(rect.width * H / W * ratio);
    ctx.setTransform(canvas.width / W, 0, 0, canvas.height / H, 0, 0);
    draw();
  }

  function aim(clientX) {
    const rect = canvas.getBoundingClientRect();
    player.target = Math.max(player.w / 2, Math.min(W - player.w / 2, (clientX - rect.left) / rect.width * W));
  }

  canvas.tabIndex = 0;
  canvas.addEventListener('pointermove', e => aim(e.clientX));
  canvas.addEventListener('pointerdown', e => { aim(e.clientX); canvas.setPointerCapture?.(e.pointerId); });
  document.addEventListener('keydown', e => {
    if (e.target !== canvas && e.target !== document.body) return;
    if (e.key === ' ' || e.key === 'Spacebar') {
      e.preventDefault();
      if (state === 'start' || state === 'over') start(); else pause(state === 'playing');
    }
    if (state !== 'playing') return;
    if (['ArrowLeft', 'a', 'A'].includes(e.key)) { e.preventDefault(); player.target = Math.max(player.w / 2, player.target - 90); }
    if (['ArrowRight', 'd', 'D'].includes(e.key)) { e.preventDefault(); player.target = Math.min(W - player.w / 2, player.target + 90); }
  });
  $$('[data-start]').forEach(button => button.addEventListener('click', start));
  $('[data-resume]').addEventListener('click', () => pause(false));
  pauseButton.addEventListener('click', () => pause(state === 'playing'));
  document.addEventListener('visibilitychange', () => { if (document.hidden) pause(true); });
  window.addEventListener('resize', resize);
  mark.addEventListener('load', draw);
  resize();
})();
