(() => {
  'use strict';
  const reducedQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  const reduced = () => reducedQuery.matches || document.documentElement.classList.contains('motion-paused');
  const isMobile = () => window.innerWidth < 900;
  const clamp = (v, min, max) => Math.min(max, Math.max(min, v));
  const easeOutCubic = x => 1 - Math.pow(1 - x, 3);

  /* ── Motion 1: the product follows the scroll through four scenes ── */
  const stage = document.querySelector('.stage');
  if (stage) {
    const SCENES = 4;
    const PROPS = ['y', 'h', 'x', 'r', 'u0', 'u1', 'u2'];  // u0-u2: how far each jelly has dived into the bottle
    const pin = stage.querySelector('.stage-pin');
    const bottle = stage.querySelector('#bottle');
    const shots = [...bottle.querySelectorAll('img')];
    const dives = [...stage.querySelectorAll('.dive-jelly')];
    const easeInOut = x => (x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2);
    const lines = [...stage.querySelectorAll('.mega-line')];
    const panels = [...stage.querySelectorAll('.panel')];
    const panelBox = stage.querySelector('.panels');
    const notes = [...stage.querySelectorAll('.note')];
    const jumps = [...stage.querySelectorAll('[data-go]')];
    const header = document.querySelector('.site-header');
    let keys = [];
    let target = null;
    let cur = null;
    let scene = -1;
    let followFrame = 0;
    let scrollFrame = 0;
    let entered = 0;

    // Each giant line fills the stage width, capped at 19% (mobile 13%) of the screen height.
    function fitMega() {
      const width = pin.clientWidth * .94;
      const maxSize = pin.clientHeight * (isMobile() ? .13 : .19) / .84;
      lines.forEach(line => {
        const inner = line.querySelector('.mega-inner');
        let size = 100;
        // Text width is not perfectly linear in font size (hinting, spacing), so correct twice.
        for (let pass = 0; pass < 3; pass++) {
          line.style.setProperty('--fs', `${size}px`);
          const w = inner.getBoundingClientRect().width;
          if (!w) break;
          size = Math.min(size * width / w, maxSize);
        }
        line.style.setProperty('--fs', `${size}px`);
      });
    }

    // Pre-compute the product pose for every scene so it stands in the space the typography leaves free.
    function measure() {
      const headerHeight = header ? header.offsetHeight : 0;
      stage.style.setProperty('--hh', `${headerHeight}px`);
      // Mobile: the bottom-zone line sits above the fixed panel. Desktop: the first panel sits above that line.
      stage.style.setProperty('--pb', `${panelBox.offsetHeight}px`);
      fitMega();
      stage.style.setProperty('--line0', `${lines[0].offsetHeight}px`);
      const vw = pin.clientWidth;
      const vh = pin.clientHeight;
      const mobile = isMobile();
      const maxH = Math.min(vw * (mobile ? .62 : .3), vh * .62);  // the box is square (ratio 1)
      const panelTop = mobile ? panelBox.offsetTop + 30 : vh * .95;
      keys = lines.map((line, i) => {
        const top = line.offsetTop;
        const height = line.offsetHeight;
        if (line.dataset.zone === 'bottom') {
          const spaceTop = headerHeight + vh * .02;
          const floor = top + height * .14;  // the base overlaps the top of the letters a little
          const h = Math.max(80, Math.min(maxH, floor - spaceTop));
          return {y: floor - h, h, x: mobile ? 0 : vw * .035, r: -14};
        }
        const spaceTop = top + height + vh * .015;
        const spaceBottom = mobile ? panelTop : vh * .95;
        let h = Math.max(80, Math.min(maxH, spaceBottom - spaceTop));
        if (i === 3) h *= .84;
        return {y: spaceTop + (spaceBottom - spaceTop - h) / 2, h, x: 0, r: i === 1 ? -5 : 0};
      });
      placeNotes(vw);
      update();
    }

    // Note cards pop out around the scene-3 (jelly) pose.
    function placeNotes(vw) {
      const k = keys[2];
      const cx = vw / 2 + k.x;
      const cy = k.y + k.h * .62;
      const spread = Math.max(k.h * .62, 120);
      [[-1, -.55], [1, -.2], [-.75, .55]].forEach(([dx, dy], i) => {
        const note = notes[i];
        if (!note) return;
        const half = note.offsetWidth / 2 + 8;
        note.style.left = `${clamp(cx + dx * spread, half, vw - half - (isMobile() ? 30 : 0))}px`;
        note.style.top = `${cy + dy * spread * .7}px`;
      });
    }

    function progress() {
      const total = stage.offsetHeight - window.innerHeight;
      return total > 0 ? clamp(-stage.getBoundingClientRect().top / total, 0, 1) : 0;
    }

    function setScene(n) {
      if (n === scene) return;
      const previous = scene;
      scene = n;
      stage.dataset.scene = String(n);
      lines.forEach((line, i) => { line.classList.toggle('is-on', i === n); line.classList.toggle('is-off', i === previous); });
      panels.forEach((panel, i) => panel.classList.toggle('is-on', i === n));
      if (n > 0) setShot(String(n));
      jumps.forEach((button, i) => (i === n ? button.setAttribute('aria-current', 'true') : button.removeAttribute('aria-current')));
    }

    function setShot(key) {
      shots.forEach(shot => shot.classList.toggle('is-on', shot.dataset.shot === key));
    }

    // Scene 1: lime, lemon and cherry jellies arc into the bottle one after another; the drink takes each flavor.
    function placeJellies() {
      const vw = pin.clientWidth;
      const mobile = isMobile();
      const h = cur.h;
      const cx = vw / 2 + cur.x;
      const oy = cur.y + h * .6;  // matches the bottle's transform-origin (50% 60%)
      const th = cur.r * Math.PI / 180;
      const rot = (dx, dy) => [cx + dx * Math.cos(th) - dy * Math.sin(th), oy + dx * Math.sin(th) + dy * Math.cos(th)];
      const [mx, my] = rot(0, -h * .56);  // bottle mouth
      const [ex, ey] = rot(0, -h * .12);  // down into the drink
      const w = h * (mobile ? .5 : .46);
      const top = (header ? header.offsetHeight : 0) + w * .35;
      let count = 0;
      [[-.62, -.5], [.62, -.66], [.7, -.08]].forEach(([dx, dy], k) => {
        const el = dives[k];
        if (!el) return;
        const u = cur[`u${k}`];
        if (u >= .9) count++;
        const sx = clamp(cx + dx * h * (mobile ? .75 : 1), w / 2 + 8, vw - w / 2 - (mobile ? 34 : 110));
        const sy = Math.max(oy + dy * h, top);
        const dir = k % 2 ? -1 : 1;
        let x, y, s, spin;
        if (u < .75) {
          // Arc up and over into the mouth, shrinking and tumbling on the way.
          const v = easeInOut(u / .75);
          const qx = (sx + mx) / 2, qy = Math.min(sy, my) - h * .28;
          x = (1 - v) ** 2 * sx + 2 * (1 - v) * v * qx + v * v * mx;
          y = (1 - v) ** 2 * sy + 2 * (1 - v) * v * qy + v * v * my;
          s = 1 - .72 * v;
          spin = 220 * v * dir;
        } else {
          // Through the neck and down into the drink, behind the glass.
          const v = (u - .75) / .25;
          x = mx + (ex - mx) * v;
          y = my + (ey - my) * v;
          s = .28 - .1 * v;
          spin = (220 + 40 * v) * dir;
        }
        el.style.width = `${w}px`;
        el.style.transform = `translate(${x - w / 2}px, ${y - w * .36}px) rotate(${spin}deg) scale(${s})`;
        el.style.opacity = u >= .995 ? '0' : '1';
        el.classList.toggle('is-inside', u >= .75);
        el.classList.toggle('is-diving', u > .01);
      });
      if (scene === 0) setShot(`0-${Math.max(0, count - 1)}`);
      if (count > entered && !reduced()) {
        bottle.classList.remove('is-gulp');
        void bottle.offsetWidth;
        bottle.classList.add('is-gulp');
      }
      entered = count;
    }

    function update() {
      scrollFrame = 0;
      if (!keys.length) return;
      const p = progress();
      const seg = p * SCENES;
      const i = Math.min(Math.floor(seg), SCENES - 1);
      const t = Math.min(seg - i, 1);
      const a = keys[i];
      const sink = window.innerHeight * .035;
      const wobble = reduced() ? 0 : Math.sin(p * 18) * 1.5;
      if (t < .6 || i === SCENES - 1) {
        // Hold the scene, sinking slowly while the reader scrolls.
        target = {y: a.y + sink * Math.min(t / .6, 1), h: a.h, x: a.x, r: a.r + wobble};
      } else {
        const b = keys[i + 1];
        const e = easeOutCubic((t - .6) / .4);
        target = {y: a.y + sink + (b.y - a.y - sink) * e, h: a.h + (b.h - a.h) * e, x: a.x + (b.x - a.x) * e, r: a.r + (b.r - a.r) * e + wobble};
      }
      // Jellies dive in one by one during the first scene (lime, then lemon, then cherry).
      // All three are in before the bottle starts moving to the next scene (t = .6).
      [0, 1, 2].forEach(k => { target[`u${k}`] = clamp((seg - (.04 + k * .17)) / .28, 0, 1); });
      // The copy changes while the product is still on its way.
      setScene(Math.min(SCENES - 1, Math.floor(seg + .2)));
      if (!followFrame) followFrame = requestAnimationFrame(follow);
    }

    function follow() {
      followFrame = 0;
      if (!cur || reduced()) cur = {...target};
      else PROPS.forEach(k => { cur[k] += (target[k] - cur[k]) * .16; });
      bottle.style.setProperty('--by', `${cur.y}px`);
      bottle.style.setProperty('--bh', `${cur.h}px`);
      bottle.style.setProperty('--bx', `${cur.x}px`);
      bottle.style.setProperty('--br', `${cur.r}deg`);
      if (dives.length) placeJellies();
      if (PROPS.some(k => Math.abs(target[k] - cur[k]) >= .1)) followFrame = requestAnimationFrame(follow);
    }

    window.addEventListener('scroll', () => { if (!scrollFrame) scrollFrame = requestAnimationFrame(update); }, {passive: true});
    let resizeFrame = 0;
    window.addEventListener('resize', () => { cancelAnimationFrame(resizeFrame); resizeFrame = requestAnimationFrame(measure); });
    window.addEventListener('load', measure);
    if (document.fonts) {
      // The display font loads lazily, so wait for it explicitly before trusting the line widths.
      document.fonts.load(`400 100px ${getComputedStyle(lines[0]).fontFamily}`).then(measure, () => {});
      document.fonts.ready.then(measure);
      document.fonts.addEventListener?.('loadingdone', measure);
    }
    jumps.forEach(button => button.addEventListener('click', () => {
      const n = Number(button.dataset.go);
      const total = stage.offsetHeight - window.innerHeight;
      const top = stage.getBoundingClientRect().top + window.scrollY + total * ((n + .3) / SCENES);
      window.scrollTo({top, behavior: reduced() ? 'auto' : 'smooth'});
    }));
    measure();
  }

  /* ── Motion 2: mist particles ── */
  function sprite(size, paint) {
    const c = document.createElement('canvas');
    c.width = c.height = size;
    paint(c.getContext('2d'), size);
    return c;
  }

  class Mist {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.parts = [];
      this.beads = [];
      this.frame = 0;
      this.loop = this.loop.bind(this);
      this.haze = sprite(64, (g, s) => {
        const grad = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
        grad.addColorStop(0, 'rgba(255,255,255,1)');
        grad.addColorStop(.45, 'rgba(255,255,255,.45)');
        grad.addColorStop(1, 'rgba(255,255,255,0)');
        g.fillStyle = grad;
        g.fillRect(0, 0, s, s);
      });
      this.drop = sprite(32, (g, s) => {
        const body = g.createRadialGradient(s * .45, s * .45, s * .05, s / 2, s / 2, s / 2);
        body.addColorStop(0, 'rgba(255,255,255,.12)');
        body.addColorStop(.75, 'rgba(255,255,255,.28)');
        body.addColorStop(.92, 'rgba(255,255,255,.6)');
        body.addColorStop(1, 'rgba(255,255,255,0)');
        g.fillStyle = body;
        g.beginPath(); g.arc(s / 2, s / 2, s / 2, 0, Math.PI * 2); g.fill();
        g.fillStyle = 'rgba(255,255,255,.95)';
        g.beginPath(); g.ellipse(s * .34, s * .3, s * .12, s * .07, -.7, 0, Math.PI * 2); g.fill();
      });
      this.resize();
    }

    resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = this.canvas.getBoundingClientRect();
      this.w = rect.width;
      this.h = rect.height;
      this.canvas.width = Math.round(rect.width * dpr);
      this.canvas.height = Math.round(rect.height * dpr);
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    burst(nx, ny, tx, ty, settle) {
      this.settle = settle;
      const scale = isMobile() ? .6 : 1;
      const dist = Math.hypot(tx - nx, ty - ny);
      const base = Math.atan2(ty - ny, tx - nx);
      const add = (count, make) => { for (let n = 0; n < Math.round(count * scale); n++) this.parts.push(make()); };
      const launch = (spread, drag, min, max) => {
        const angle = base + (Math.random() * 2 - 1) * spread;
        const speed = dist * (1 - drag) * (min + Math.random() * (max - min));
        return {x: nx, y: ny, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed, delay: Math.floor(Math.random() * 23), drag, life: 1};
      };
      add(2400, () => ({...launch(.3, .955, .45, 1.35), kind: 'aerosol', decay: .01 + Math.random() * .01}));
      add(46, () => ({...launch(.3, .96, .25, .9), kind: 'haze', r: 16 + Math.random() * 18, decay: .003 + Math.random() * .003}));
      add(60, () => ({...launch(.24, .975, .65, 1.25), kind: 'drop', size: 5 + Math.random() * 7, decay: 0}));
      if (!this.frame) this.frame = requestAnimationFrame(this.loop);
    }

    reset() {
      this.parts = [];
      this.beads = [];
      cancelAnimationFrame(this.frame);
      this.frame = 0;
      this.ctx.clearRect(0, 0, this.w, this.h);
    }

    loop(now) {
      const ctx = this.ctx;
      const live = [];
      for (const p of this.parts) {
        if (p.delay > 0) { p.delay--; live.push(p); continue; }
        p.vx *= p.drag;
        p.vy = p.vy * p.drag + .025;
        if (p.kind === 'haze') { p.vy -= .04; p.r += .22; }
        p.x += p.vx;
        p.y += p.vy;
        p.life -= p.decay;
        if (p.kind === 'drop' && Math.hypot(p.vx, p.vy) < .35) {
          if (this.settle?.(p.x, p.y)) {
            this.beads.push({x: p.x, y: p.y, size: p.size * .8, born: now, phase: Math.random() * 6.28});
            if (this.beads.length > 160) this.beads.shift();
          }
          continue;
        }
        if (p.life > 0 && p.y < this.h + 40) live.push(p);
      }
      this.parts = live;
      this.beads = this.beads.filter(b => now - b.born < 14000);

      ctx.clearRect(0, 0, this.w, this.h);
      ctx.globalCompositeOperation = 'source-over';
      for (const p of live) {
        if (p.kind !== 'haze' || p.delay > 0) continue;
        ctx.globalAlpha = .28 * Math.max(p.life, 0);
        ctx.drawImage(this.haze, p.x - p.r, p.y - p.r, p.r * 2, p.r * 2);
      }
      ctx.globalCompositeOperation = 'lighter';
      for (const b of this.beads) {
        const age = (now - b.born) / 14000;
        ctx.globalAlpha = (1 - age) * (.55 + .45 * Math.sin(now / 180 + b.phase));
        ctx.drawImage(this.drop, b.x - b.size / 2, b.y - b.size / 2, b.size, b.size);
      }
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1;
      // Aerosol as motion streaks, batched into fast and slow strokes.
      for (const [slow, alpha] of [[false, .28], [true, .18]]) {
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        for (const p of live) {
          if (p.kind !== 'aerosol' || p.delay > 0) continue;
          const speed = Math.hypot(p.vx, p.vy);
          if ((speed < .6) !== slow || p.life < .05) continue;
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x - p.vx * 1.8, p.y - p.vy * 1.8 - (slow ? .8 : 0));
        }
        ctx.stroke();
      }
      ctx.globalAlpha = .9;
      for (const p of live) {
        if (p.kind !== 'drop' || p.delay > 0) continue;
        ctx.drawImage(this.drop, p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
      }
      ctx.globalAlpha = 1;
      this.frame = live.length || this.beads.length ? requestAnimationFrame(this.loop) : 0;
      if (!this.frame) ctx.clearRect(0, 0, this.w, this.h);
    }
  }

  /* ── Motion 2: the spritz demo ── */
  const plate = document.querySelector('[data-plate]');
  if (plate) {
    const box = plate.querySelector('.plate-stage');
    const photo = box.querySelector('.plate-photo');
    const product = box.querySelector('.plate-bottle');
    const mist = new Mist(box.querySelector('#plate-mist'));
    const button = plate.querySelector('[data-spray]');
    const phraseEl = plate.querySelector('[data-phrase]');
    const countEl = plate.querySelector('[data-count]');
    const phrases = [...plate.querySelectorAll('[data-phrases] li')].map(li => li.textContent);
    const fallback = plate.querySelector('[data-phrase-default]').textContent;
    const intro = plate.querySelector('[data-phrase-intro]').textContent;
    const TILT = -38 * Math.PI / 180;
    let count = 0;
    let lastPress = 0;
    let timers = [];

    // Drops that land on the jellies (an ellipse over the photo) stay as sparkling beads.
    const settle = (x, y) => {
      const cx = mist.w * .5, cy = mist.h * .6, rx = mist.w * .44, ry = mist.h * .3;
      return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1;
    };

    function fire() {
      // Nozzle: product centre plus 46% of its height along the tilt (layout box, so the in-flight transform doesn't matter).
      const cx = product.offsetLeft + product.offsetWidth / 2;
      const cy = product.offsetTop + product.offsetHeight / 2;
      const half = product.offsetHeight * .46;
      mist.burst(cx + Math.sin(TILT) * half, cy - Math.cos(TILT) * half, mist.w * .5, mist.h * .56, settle);
      photo.classList.remove('is-fresh');
      void photo.offsetWidth;
      photo.classList.add('is-fresh');
    }

    function spray(force = false) {
      if (reduced() && !force) return;
      const now = performance.now();
      if (now - lastPress < 450) return;
      lastPress = now;
      timers.forEach(clearTimeout);
      product.classList.remove('is-spraying');
      void product.offsetWidth;
      product.classList.add('is-spraying');
      timers = [setTimeout(fire, 380), setTimeout(() => product.classList.remove('is-spraying'), 1400)];
      count++;
      countEl.textContent = String(count);
      phraseEl.textContent = phrases[count - 1] || fallback;
      button.querySelector('[data-label-first]').hidden = true;
      button.querySelector('[data-label-again]').hidden = false;
    }

    // A press by the user always plays, even with reduced motion.
    button.addEventListener('click', () => spray(true));
    plate.querySelector('[data-reset]').addEventListener('click', () => {
      timers.forEach(clearTimeout);
      product.classList.remove('is-spraying');
      photo.classList.remove('is-fresh');
      mist.reset();
      count = 0;
      countEl.textContent = '0';
      phraseEl.textContent = intro;
      button.querySelector('[data-label-first]').hidden = false;
      button.querySelector('[data-label-again]').hidden = true;
    });
    window.addEventListener('resize', () => mist.resize());
  }

})();
