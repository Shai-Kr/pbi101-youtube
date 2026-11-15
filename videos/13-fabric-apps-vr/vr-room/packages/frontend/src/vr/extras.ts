// The showpieces: Saturn and the region planets, the guessing game,
// the wrist watch, the "inside" wall, the bin and the words on the floor.

import * as THREE from 'three';

import { CATEGORY_COLORS, filterText, fmtPct, MEASURES, memberLabel, MONTHS, REGION_COLORS } from './data';
import type { Engine } from './engine';
import type { Store } from './store';
import { makeLabel, setLabel } from './text';
import { button, easeBack, glow, mat, panel, pedestal, row, softBox, tween } from './ui';

function noiseTexture(base: string, marks: string[], bands: boolean): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 128;
  const x = c.getContext('2d')!;
  x.fillStyle = base;
  x.fillRect(0, 0, 256, 128);
  if (bands) {
    for (let y = 0; y < 128; y += 6 + Math.random() * 10) {
      x.fillStyle = marks[Math.floor(Math.random() * marks.length)];
      x.globalAlpha = 0.35 + Math.random() * 0.4;
      x.fillRect(0, y, 256, 3 + Math.random() * 9);
    }
  } else {
    for (let i = 0; i < 46; i++) {
      x.fillStyle = marks[Math.floor(Math.random() * marks.length)];
      x.globalAlpha = 0.25 + Math.random() * 0.4;
      x.beginPath();
      x.ellipse(Math.random() * 256, Math.random() * 128, 6 + Math.random() * 26, 4 + Math.random() * 12, Math.random() * 3, 0, Math.PI * 2);
      x.fill();
    }
  }
  x.globalAlpha = 1;
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.userData.shared = true;
  return t;
}

// ------------------------------------------------------------------------------------- Saturn (space)

/** Saturn is the whole company; its ring is the twelve months of the year, each piece named and valued. */
export class Saturn {
  readonly group = new THREE.Group();
  private ring = new THREE.Group();
  private labels = new THREE.Group();
  private caption: THREE.Mesh;
  private ball: THREE.Mesh;
  private readonly tilt = 1.02;

  constructor(
    private engine: Engine,
    private store: Store
  ) {
    this.group.position.set(0, 19, -34);
    this.ball = new THREE.Mesh(
      new THREE.SphereGeometry(4.6, 40, 28),
      mat(0xffffff, { map: noiseTexture('#d9a03c', ['#a8661f', '#f6d58a', '#7d4a18', '#eab552', '#fff0c4'], true) })
    );
    const halo = glow(22, 0xffd58a, 0.45);
    halo.position.z = -3;
    this.ring.rotation.x = -Math.PI / 2 + this.tilt;
    this.group.add(halo, this.ball, this.ring, this.labels);
    this.caption = makeLabel(' ', { h: 1.5, weight: '800', px: 96 });
    this.caption.position.set(0, 13.8, 0);
    this.caption.rotation.x = 0.45;
    this.group.add(this.caption);
    store.subscribe(() => this.render());
    engine.frame.push((dt) => (this.ball.rotation.y += dt * 0.05));
    this.render();
  }

  render(): void {
    const { engine, store } = this;
    const cube = store.cube;
    const m = MEASURES[store.measure];
    engine.clear(this.ring);
    engine.clear(this.labels);
    const f = { ...store.filter };
    delete f.month;
    const year = (f.year as number | undefined) ?? cube.latestYear;
    const rows = cube.by('month', { ...f, year });
    const max = Math.max(1, ...rows.map((r) => m.of(r.totals)));
    const total = rows.reduce((s, r) => s + m.of(r.totals), 0);
    const seg = (Math.PI * 2) / 12;
    const rot = new THREE.Euler(-Math.PI / 2 + this.tilt, 0, 0);
    rows.forEach((r, i) => {
      const v = m.of(r.totals);
      const outer = 7.4 + (v / max) * 4.4;
      // January starts at the top and the year runs clockwise, like a clock
      const start = Math.PI / 2 - (i + 1) * seg + 0.035;
      const geo = new THREE.RingGeometry(6.3, v > 0 ? outer : 7.0, 12, 1, start, seg - 0.07);
      const sel = store.filter.month === r.key;
      const dim = store.filter.month !== undefined && !sel;
      const mesh = new THREE.Mesh(
        geo,
        mat(v > 0 ? (sel ? 0xffffff : i % 2 ? 0xffc04a : 0xff9f2e) : 0x3a4266, { opacity: dim ? 0.25 : v > 0 ? 0.9 : 0.4, basic: true, side: THREE.DoubleSide })
      );
      engine.register(mesh, {
        tip: v > 0 ? `${MONTHS[i]} ${year} · ${m.fmt(v)}` : `${MONTHS[i]} ${year} · no data yet`,
        select: v > 0 ? () => store.toggle('month', r.key) : undefined,
      });
      this.ring.add(mesh);
      const a = Math.PI / 2 - (i + 0.5) * seg;
      const rad = (v > 0 ? outer : 7.0) + 1.5;
      const p = new THREE.Vector3(Math.cos(a) * rad, Math.sin(a) * rad, 0).applyEuler(rot);
      const lab = makeLabel(v > 0 ? `${MONTHS[i].toUpperCase()}\n${m.fmt(v)}` : `${MONTHS[i].toUpperCase()}\n-`, { h: 0.82, color: v > 0 ? '#fff6dc' : '#9aa3c4', weight: '800', px: 80 });
      lab.position.copy(p);
      lab.position.z += 0.3;
      lab.rotation.x = 0.45; // leans down towards the viewer on the deck
      this.labels.add(lab);
    });
    setLabel(this.caption, `AURORA ${year} · ${m.fmt(total)}\nthe ring is the year · one piece per month`);
  }
}

// ------------------------------------------------------------------------------------- planets (space)

/** One planet per region: size = its share, speed = its growth against last year, moons = product categories. */
export class Planets {
  readonly group = new THREE.Group();
  private bodies: { g: THREE.Group; ball: THREE.Mesh; radius: number; angle: number; speed: number; r: number; y: number; moons: THREE.Mesh[]; paused: boolean; held: boolean }[] = [];
  private textures = new Map<string, THREE.CanvasTexture>();

  constructor(
    private engine: Engine,
    private store: Store
  ) {
    store.subscribe(() => this.render());
    engine.frame.push((dt, t) => this.update(dt, t));
    this.render();
  }

  private tex(region: string): THREE.CanvasTexture {
    let t = this.textures.get(region);
    if (!t) {
      const c = new THREE.Color(REGION_COLORS[region] ?? 0x93c5fd);
      const light = '#' + c.clone().offsetHSL(0.02, 0, 0.16).getHexString();
      const dark = '#' + c.clone().offsetHSL(-0.03, 0, -0.16).getHexString();
      t = noiseTexture('#' + c.getHexString(), [light, dark, '#ffffff'], region.length % 2 === 0);
      this.textures.set(region, t);
    }
    return t;
  }

  render(): void {
    const { engine, store } = this;
    const cube = store.cube;
    const m = MEASURES[store.measure];
    const old = this.bodies;
    engine.clear(this.group);
    this.bodies = [];
    const f = { ...store.filter };
    delete f.region;
    const rows = cube.by('region', f);
    const sum = rows.reduce((s, r) => s + m.of(r.totals), 0) || 1;
    rows.forEach((r, i) => {
      const v = m.of(r.totals);
      const share = v / sum;
      const yoy = cube.yoy({ ...f, region: r.key }, store.measure);
      const radius = 0.5 + 1.15 * Math.sqrt(share);
      const g = new THREE.Group();
      const sel = store.filter.region === r.key;
      const dim = store.filter.region !== undefined && !sel;
      const ball = new THREE.Mesh(new THREE.SphereGeometry(radius, 32, 22), mat(0xffffff, { map: this.tex(String(r.key)), opacity: dim ? 0.3 : 1 }));
      const halo = glow(radius * 4.4, REGION_COLORS[String(r.key)] ?? 0x93c5fd, dim ? 0.15 : 0.55);
      const holder = new THREE.Group();
      halo.position.z = -radius * 0.9;
      holder.add(halo);
      const lab = makeLabel(`${r.key}\n${m.fmt(v)} · ${isFinite(yoy.pct) ? fmtPct(yoy.pct, true) : 'n/a'}`, { h: 0.42, weight: '800', px: 80 });
      lab.position.y = -radius - 0.75;
      holder.add(lab);
      engine.billboards.add(holder);
      g.add(holder, ball);
      const moons: THREE.Mesh[] = [];
      const cats = cube.by('category', { ...f, region: r.key });
      const cmax = Math.max(1, ...cats.map((c) => m.of(c.totals)));
      cats.forEach((c) => {
        const moon = new THREE.Mesh(new THREE.SphereGeometry(0.13 + 0.2 * Math.sqrt(m.of(c.totals) / cmax), 16, 12), mat(CATEGORY_COLORS[String(c.key)] ?? 0xcbd5e1, { opacity: dim ? 0.3 : 1 }));
        g.add(moon);
        moons.push(moon);
      });

      const prev = old[i];
      const body = {
        g,
        ball,
        radius,
        angle: prev ? prev.angle : (i / rows.length) * Math.PI * 2 + 0.75,
        // growth turns faster, shrinking turns slower (never backwards)
        speed: 0.045 * THREE.MathUtils.clamp(1 + (isFinite(yoy.pct) ? yoy.pct * 6 : 0), 0.25, 2.5),
        r: 11.5,
        y: 6.4 + (i % 2) * 1.5,
        moons,
        paused: false,
        held: false,
      };
      engine.register(g, {
        tip: () => `${r.key} · ${m.fmt(v)} · ${fmtPct(share)} of the total${isFinite(yoy.pct) ? ' · ' + fmtPct(yoy.pct, true) + ' vs last year' : ''}`,
        select: () => store.toggle('region', r.key),
        enter: () => engine.fade(() => store.enter('region', r.key)),
        hover: (on) => (body.paused = on),
        grab: {
          onGrab: () => (body.held = true),
          onRelease: () => {
            this.group.attach(g);
            const from = g.position.clone();
            const to = new THREE.Vector3(Math.sin(body.angle) * body.r, body.y, -Math.cos(body.angle) * body.r);
            tween(1.4, (k) => g.position.lerpVectors(from, to, k), () => (body.held = false));
          },
        },
      });
      this.group.add(g);
      this.bodies.push(body);
    });
    this.update(0, 0);
  }

  private update(dt: number, t: number): void {
    for (const b of this.bodies) {
      if (!b.paused && !b.held) b.angle += b.speed * dt;
      if (!b.held) b.g.position.set(Math.sin(b.angle) * b.r, b.y, -Math.cos(b.angle) * b.r);
      b.ball.rotation.y += dt * 0.12;
      b.moons.forEach((moon, i) => {
        const a = t * (0.45 + i * 0.12) + i * 1.7;
        const d = b.radius + 0.5 + i * 0.22;
        moon.position.set(Math.cos(a) * d, Math.sin(a * 0.7) * 0.25, Math.sin(a) * d);
      });
    }
  }
}

// ------------------------------------------------------------------------------------- guessing game

/** Guess a number before it is shown: mark a height on the empty column, then reveal the real one. */
export class GuessGame {
  readonly group = new THREE.Group();
  private question: THREE.Mesh;
  private score: THREE.Mesh;
  private marker: THREE.Mesh;
  private real: THREE.Mesh;
  private guessLabel: THREE.Mesh;
  private max = 1;
  private answer = 0;
  private guess = -1;
  private revealed = false;
  private total = 0;
  private rounds = 0;
  private what = '';
  private readonly H = 1.8;
  private readonly baseY = 0.6;
  private ticks = new THREE.Group();

  constructor(
    private engine: Engine,
    private store: Store
  ) {
    this.group.add(pedestal(0.6, this.baseY));

    const glass = new THREE.Mesh(softBox(0.8, this.H, 0.8, 0.08), mat(0x9cc2ff, { opacity: 0.22 }));
    glass.position.y = this.baseY;
    engine.register(glass, {
      tip: 'Point at the height you guess and pull the trigger',
      select: (hand) => {
        if (this.revealed) return;
        const local = glass.worldToLocal(hand.hoverPoint.clone());
        this.guess = THREE.MathUtils.clamp(local.y / this.H, 0, 1) * this.max;
        this.paint();
      },
    });
    this.group.add(glass, this.ticks);

    this.marker = new THREE.Mesh(softBox(0.98, 0.06, 0.98, 0.03), mat(0xfbbf24));
    this.marker.visible = false;
    this.real = new THREE.Mesh(softBox(0.62, 1, 0.62, 0.1), mat(0x34d399));
    this.real.position.y = this.baseY;
    this.real.visible = false;
    this.group.add(this.marker, this.real);

    this.guessLabel = makeLabel(' ', { h: 0.13, color: '#1a1200', weight: '800', px: 64, bg: '#fde68a' });
    const holder = new THREE.Group();
    this.question = makeLabel(' ', { h: 0.14, weight: '700', px: 68 });
    this.score = makeLabel('Score 0', { h: 0.13, color: '#a9bdf0', weight: '700', px: 60 });
    const title = makeLabel('GUESS FIRST', { h: 0.2, weight: '800', color: '#ffd58a', px: 80 });
    title.position.y = 1.1;
    this.question.position.y = 0.62;
    this.score.position.y = 0.1;
    const back = panel(4.4, 1.6, { fill: 'rgba(18,24,60,0.9)' });
    back.position.set(0, 0.62, -0.02);
    holder.add(back, title, this.question, this.score);
    holder.position.y = this.baseY + this.H + 0.35;
    engine.billboards.add(holder);
    this.group.add(holder, this.guessLabel);

    const reveal = button(engine, 'Reveal', () => this.reveal(), { h: 0.13, plate: 0x1f7a5f });
    const next = button(engine, 'Next question', () => this.next(), { h: 0.13 });
    const r = row([reveal, next], 0.14);
    r.position.set(0, 0.3, 0.75);
    this.group.add(r);
    this.next();
  }

  private next(): void {
    const cube = this.store.cube;
    const m = MEASURES.revenue;
    const region = cube.regions[Math.floor(Math.random() * cube.regions.length)];
    const cat = cube.categories[Math.floor(Math.random() * cube.categories.length)];
    const year = cube.years[Math.floor(Math.random() * cube.years.length)];
    this.answer = cube.measure('revenue', { region, category: cat, year });
    // the scale tops out at a round number above the biggest answer for the same category
    let big = 0;
    for (const r of cube.regions) for (const y of cube.years) big = Math.max(big, cube.measure('revenue', { region: r, category: cat, year: y }));
    const unit = Math.pow(10, Math.floor(Math.log10(big)));
    this.max = Math.ceil(big / unit) * unit;
    this.what = `${cat} in ${region}, ${year}`;
    this.guess = -1;
    this.revealed = false;
    this.real.visible = false;
    this.marker.visible = false;
    setLabel(this.guessLabel, ' ');
    this.guessLabel.visible = false;
    setLabel(this.question, `How much revenue? ${this.what}\nPoint at a height on the glass column and pull the trigger`);
    this.engine.clear(this.ticks);
    for (let i = 0; i <= 4; i++) {
      const t = makeLabel(m.fmt((this.max * i) / 4), { h: 0.12, color: '#c5d3f5', weight: '700', px: 56 });
      t.position.set(-0.85, this.baseY + (this.H * i) / 4, 0);
      this.ticks.add(t);
    }
  }

  private paint(): void {
    this.marker.visible = this.guess >= 0;
    this.marker.position.y = this.baseY + (this.guess / this.max) * this.H - 0.03;
    this.guessLabel.visible = this.guess >= 0;
    setLabel(this.guessLabel, `your guess ${MEASURES.revenue.fmt(this.guess)}`);
    this.guessLabel.position.set(0.55 + this.guessLabel.userData.w / 2, this.marker.position.y + 0.03, 0.4);
  }

  private reveal(): void {
    if (this.revealed) return;
    if (this.guess < 0) {
      setLabel(this.question, `First mark your guess on the glass column\n${this.what}`);
      return;
    }
    this.revealed = true;
    this.real.visible = true;
    const h = Math.max((this.answer / this.max) * this.H, 0.02);
    tween(1.0, (k) => this.real.scale.set(1, h * k + 0.001, 1), undefined, easeBack);
    const err = Math.abs(this.guess - this.answer) / this.answer;
    const pts = Math.max(0, Math.round(100 - err * 100));
    this.total += pts;
    this.rounds++;
    setLabel(this.question, `${this.what}\nReal: ${MEASURES.revenue.fmt(this.answer)} · you were ${fmtPct(err)} off · +${pts} points`);
    setLabel(this.score, `Score ${this.total} · ${this.rounds} round${this.rounds === 1 ? '' : 's'} · average ${Math.round(this.total / this.rounds)}`);
  }
}

// ------------------------------------------------------------------------------------- wrist watch

/** A small panel on the left wrist: what is filtered now, the number, and how it compares with last year. */
export class Watch {
  readonly panel: THREE.Mesh;

  constructor(
    engine: Engine,
    private store: Store
  ) {
    this.panel = makeLabel(' ', { h: 0.032, bg: 'rgba(12,18,44,0.95)', px: 56, weight: '700' });
    this.panel.rotation.set(-1.1, 0, 0);
    this.panel.position.set(0, 0.08, 0.12);
    const attach = () => {
      const left = engine.hands.find((h) => h.side === 'left') ?? engine.hands[0];
      left.ray.add(this.panel);
    };
    attach();
    for (const h of engine.hands) (h.ray as THREE.Object3D<any>).addEventListener('connected', () => setTimeout(attach, 0));
    store.subscribe(() => this.render());
    this.render();
  }

  text(): string {
    const { cube, filter, measure } = this.store;
    const m = MEASURES[measure];
    const y = cube.yoy(filter, measure);
    return `${filterText(filter)}\n${m.label} ${m.fmt(m.of(cube.totals(filter)))}\nvs last year ${isFinite(y.pct) ? fmtPct(y.pct, true) : 'n/a'}`;
  }

  render(): void {
    setLabel(this.panel, this.text());
  }
}

// ------------------------------------------------------------------------------------- inside wall

/** After "going inside" a member, a soft wall in its colour surrounds the room and its name hangs overhead. */
export class InsideWall {
  readonly group = new THREE.Group();
  private wallMat: THREE.MeshBasicMaterial;
  private names: THREE.Mesh[] = [];

  constructor(private store: Store) {
    this.wallMat = new THREE.MeshBasicMaterial({ color: 0x4f8cff, transparent: true, opacity: 0.2, side: THREE.BackSide, depthWrite: false });
    const wall = new THREE.Mesh(new THREE.CylinderGeometry(16.5, 16.5, 12, 48, 1, true), this.wallMat);
    wall.position.y = 6;
    this.group.add(wall);
    for (let i = 0; i < 4; i++) {
      const l = makeLabel(' ', { h: 1.3, weight: '800', px: 96 });
      const a = (i / 4) * Math.PI * 2 + Math.PI / 4;
      l.position.set(Math.sin(a) * 15.5, 9.2, -Math.cos(a) * 15.5);
      l.rotation.y = -a;
      this.names.push(l);
      this.group.add(l);
    }
    store.subscribe(() => this.render());
    this.render();
  }

  render(): void {
    const top = this.store.inside[this.store.inside.length - 1];
    this.group.visible = !!top;
    if (!top) return;
    const color = top.dim === 'region' ? REGION_COLORS[String(top.value)] : top.dim === 'category' ? CATEGORY_COLORS[String(top.value)] : 0x9cc2ff;
    this.wallMat.color.setHex(color ?? 0x9cc2ff);
    const text = 'INSIDE · ' + this.store.inside.map((i) => memberLabel(i.dim, i.value)).join(' › ').toUpperCase() + '\nB or Y takes you back out';
    this.names.forEach((n) => setLabel(n, text));
  }
}

/** A bin: drop a board in it to remove it from the room. */
export function makeBin(): THREE.Group {
  const g = new THREE.Group();
  const pts = [new THREE.Vector2(0, 0), new THREE.Vector2(0.4, 0), new THREE.Vector2(0.56, 0.85), new THREE.Vector2(0.6, 0.9), new THREE.Vector2(0.52, 0.9), new THREE.Vector2(0.36, 0.06), new THREE.Vector2(0, 0.06)];
  const can = new THREE.Mesh(new THREE.LatheGeometry(pts, 24), mat(0x9aa3b8, { side: THREE.DoubleSide }));
  const lab = makeLabel('THE BIN\nHold a board with the grip, point here, let go', { h: 0.13, color: '#e6eeff', weight: '700', px: 60 });
  const holder = new THREE.Group();
  holder.position.y = 1.5;
  holder.add(lab);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.035, 8, 40), new THREE.MeshBasicMaterial({ color: 0x6ee7b7 }));
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 1.0;
  ring.visible = false;
  g.add(can, holder, ring);
  g.userData.labelHolder = holder;
  g.userData.ring = ring;
  return g;
}

/** Words on the floor around the start point, so it is clear what stands where. */
export function floorCompass(items: [string, number][], color: string, r = 2.5): THREE.Group {
  const g = new THREE.Group();
  for (const [text, angle] of items) {
    const arm = new THREE.Group();
    arm.rotation.y = -THREE.MathUtils.degToRad(angle);
    const lab = makeLabel(`▲\n${text}`, { h: 0.2, color, weight: '800', px: 64 });
    lab.rotation.x = -Math.PI / 2;
    lab.position.set(0, 0.07, -r);
    arm.add(lab);
    g.add(arm);
  }
  return g;
}
