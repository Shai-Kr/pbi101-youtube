// The hands-on stations: the shelf of balls (measures and members), the basket that turns what is thrown
// into it into a big answer, the scales that weigh two things, and the loaf that is really cut into parts.

import * as THREE from 'three';

import {
  CATEGORY_COLORS,
  colorOf,
  DIM_LABEL,
  filterText,
  fmtPct,
  MEASURES,
  memberLabel,
  REGION_COLORS,
  type Dim,
  type Filter,
  type MeasureKey,
} from './data';
import type { Engine } from './engine';
import type { Store } from './store';
import { makeLabel, setLabel } from './text';
import { button, easeBack, glow, mat, panel, pedestal, row, softBox, tween, STEEL } from './ui';
import { answerCard, bigBars, chip, growthChip, yearStrip, type BarItem } from './viz';

function twoLines(s: string): string {
  if (s.length <= 10 || !s.includes(' ')) return s;
  const words = s.split(' ');
  const half = Math.ceil(words.length / 2);
  return words.slice(0, half).join(' ') + '\n' + words.slice(half).join(' ');
}

// ------------------------------------------------------------------------------------------ the balls

export interface TokenInfo {
  kind: 'measure' | 'member' | 'op';
  label: string;
  measure?: MeasureKey;
  dim?: Dim;
  value?: string | number;
  op?: 'share' | 'yoy';
  color: number;
  home: THREE.Vector3;
  /** Where it is now, so the place it leaves can recalculate. */
  holder: { remove(t: THREE.Object3D): void } | null;
}

export const tokenOf = (o: THREE.Object3D): TokenInfo | undefined => o.userData.token as TokenInfo | undefined;

export class Shelf {
  readonly group = new THREE.Group();
  readonly tokens: THREE.Object3D[] = [];

  constructor(
    private engine: Engine,
    store: Store
  ) {
    const cube = store.cube;
    const back = panel(4.5, 3.05);
    back.position.set(0, 1.62, -0.2);
    this.group.add(back);
    const title = makeLabel('THE SHELF', { h: 0.2, color: '#ffd58a', weight: '800', px: 80 });
    title.position.set(0, 3.4, -0.15);
    const how = makeLabel('Point at a ball and squeeze the GRIP: it flies to your hand.\nThen point at the basket or the scales and let go.', { h: 0.11, color: '#e6eeff', weight: '600', px: 60 });
    how.position.set(0, 3.74 + 0.11, -0.15);
    title.position.y = 3.34;
    how.position.y = 3.68;
    this.group.add(title, how);

    type Item = Omit<TokenInfo, 'home' | 'holder' | 'color'>;
    const catOf = (p: string | number | undefined) => cube.products.find((x) => x.product === p)?.category ?? '';
    const rows: { caption: string; y: number; items: Item[]; color: (t: Item) => number }[] = [
      {
        caption: 'MEASURES (cubes) · and two that change the answer',
        y: 2.6,
        items: [
          ...(['revenue', 'orders', 'units', 'margin', 'marginPct', 'aov'] as MeasureKey[]).map((k) => ({ kind: 'measure' as const, label: MEASURES[k].label, measure: k })),
          { kind: 'op' as const, label: '% of total', op: 'share' as const },
          { kind: 'op' as const, label: 'vs last year', op: 'yoy' as const },
        ],
        color: (t) => (t.kind === 'op' ? 0xc4b5fd : 0xf8fafc),
      },
      {
        caption: 'REGIONS · YEARS',
        y: 2.02,
        items: [
          ...cube.regions.map((r) => ({ kind: 'member' as const, label: r, dim: 'region' as Dim, value: r })),
          ...cube.years.map((y) => ({ kind: 'member' as const, label: String(y), dim: 'year' as Dim, value: y })),
        ],
        color: (t) => (t.dim === 'region' ? (REGION_COLORS[String(t.value)] ?? 0x93c5fd) : 0xcbd5e1),
      },
      {
        caption: 'CATEGORIES',
        y: 1.44,
        items: cube.categories.map((c) => ({ kind: 'member' as const, label: c, dim: 'category' as Dim, value: c })),
        color: (t) => CATEGORY_COLORS[String(t.value)] ?? 0x93c5fd,
      },
      {
        caption: 'PRODUCTS',
        y: 0.86,
        items: cube.products.slice(0, 6).map((p) => ({ kind: 'member' as const, label: p.product, dim: 'product' as Dim, value: p.product })),
        color: (t) => CATEGORY_COLORS[catOf(t.value)] ?? 0x93c5fd,
      },
      {
        caption: '',
        y: 0.36,
        items: cube.products.slice(6).map((p) => ({ kind: 'member' as const, label: p.product, dim: 'product' as Dim, value: p.product })),
        color: (t) => CATEGORY_COLORS[catOf(t.value)] ?? 0x93c5fd,
      },
    ];

    for (const r of rows) {
      if (r.caption) {
        const cap = makeLabel(r.caption, { h: 0.075, color: '#8fa6e6', weight: '700', px: 48, align: 'left' });
        cap.position.set(-2.1 + cap.userData.w / 2, r.y + 0.27, -0.15);
        this.group.add(cap);
      }
      const step = 4.2 / r.items.length;
      r.items.forEach((info, i) => {
        const home = new THREE.Vector3(-2.1 + step * (i + 0.5), r.y, 0);
        const t = this.makeToken({ ...info, color: r.color(info), home, holder: null });
        t.position.copy(home);
        this.group.add(t);
        this.tokens.push(t);
      });
    }
  }

  private makeToken(info: TokenInfo): THREE.Object3D {
    const g = new THREE.Group();
    const ball = new THREE.Mesh(
      info.kind === 'op' ? new THREE.OctahedronGeometry(0.13, 1) : info.kind === 'measure' ? softBox(0.2, 0.2, 0.2, 0.05).translate(0, -0.1, 0) : new THREE.SphereGeometry(0.115, 20, 14),
      mat(info.color)
    );
    const name = makeLabel(twoLines(info.label), { h: 0.07, px: 52, weight: '700' });
    name.position.y = -0.16 - name.userData.hgt / 2;
    g.add(ball, name);
    g.userData.token = info;
    this.engine.billboards.add(g);
    this.engine.register(g, {
      tip: info.kind === 'measure' ? `${info.label} · a measure` : info.kind === 'op' ? `${info.label} · changes the answer` : `${info.label} · ${DIM_LABEL[info.dim!].toLowerCase()}`,
      hover: (on) => ball.scale.setScalar(on ? 1.3 : 1),
      grab: {
        pull: true,
        onGrab: () => {
          info.holder?.remove(g);
          info.holder = null;
        },
        onRelease: () => this.sendHome(g),
      },
    });
    return g;
  }

  /** A ball let go in mid-air flies back to its place on the shelf. */
  sendHome(t: THREE.Object3D): void {
    const info = tokenOf(t)!;
    info.holder?.remove(t);
    info.holder = null;
    this.group.attach(t);
    const from = t.position.clone();
    t.scale.setScalar(1);
    tween(0.5, (k) => t.position.lerpVectors(from, info.home, k));
  }
}

/** A ring of light that shows a place is ready to catch what the hand is aiming. */
function catchRing(radius: number): THREE.Mesh {
  const m = new THREE.Mesh(
    new THREE.TorusGeometry(radius, 0.035, 8, 40),
    new THREE.MeshBasicMaterial({ color: 0x6ee7b7, transparent: true, opacity: 0.95, depthWrite: false })
  );
  m.rotation.x = Math.PI / 2;
  m.visible = false;
  return m;
}

// ------------------------------------------------------------------------------------------ the basket

export class Basket {
  readonly group = new THREE.Group();
  private inside: THREE.Object3D[] = [];
  private bowl = new THREE.Group();
  private card = new THREE.Group();
  private ring: THREE.Mesh;

  constructor(
    private engine: Engine,
    private store: Store,
    private shelf: Shelf
  ) {
    this.group.add(pedestal(0.42, 0.85));
    const pts = [new THREE.Vector2(0.0, 0), new THREE.Vector2(0.42, 0.0), new THREE.Vector2(0.62, 0.22), new THREE.Vector2(0.7, 0.46), new THREE.Vector2(0.66, 0.5), new THREE.Vector2(0.58, 0.26), new THREE.Vector2(0.4, 0.06), new THREE.Vector2(0, 0.06)];
    const bowlMesh = new THREE.Mesh(new THREE.LatheGeometry(pts, 32), mat(0xffb43c, { side: THREE.DoubleSide }));
    bowlMesh.position.y = 0.85;
    // woven bands
    for (const [y, r] of [
      [1.02, 0.585],
      [1.17, 0.655],
    ]) {
      const band = new THREE.Mesh(new THREE.TorusGeometry(r, 0.022, 8, 40), mat(0xc98a1e));
      band.rotation.x = Math.PI / 2;
      band.position.y = y;
      this.group.add(band);
    }
    this.bowl.position.y = 1.0;
    this.ring = catchRing(0.78);
    this.ring.position.y = 1.38;
    this.group.add(bowlMesh, this.bowl, this.ring);

    const holder = new THREE.Group();
    holder.position.y = 1.95;
    holder.add(this.card);
    engine.billboards.add(holder);
    this.group.add(holder);

    const empty = button(engine, 'Empty the basket', () => this.empty(), { h: 0.1, plate: 0x8a4a5a, tip: 'All the balls fly back to the shelf' });
    empty.position.set(0, 0.42, 0.56);
    this.group.add(empty);

    engine.zones.push({
      center: () => this.bowl.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.2, 0)),
      radius: 0.8,
      accepts: (o) => !!tokenOf(o),
      drop: (o) => this.add(o),
      highlight: (on) => (this.ring.visible = on),
    });
    store.subscribe(() => this.compute());
    this.compute();
  }

  private add(t: THREE.Object3D): void {
    const info = tokenOf(t)!;
    info.holder = this;
    this.bowl.attach(t);
    this.inside.push(t);
    this.layout();
    this.compute();
  }

  remove(t: THREE.Object3D): void {
    this.inside = this.inside.filter((x) => x !== t);
    this.layout();
    this.compute();
  }

  empty(): void {
    for (const t of [...this.inside]) this.shelf.sendHome(t);
    this.inside = [];
    this.compute();
  }

  private layout(): void {
    const n = this.inside.length;
    this.inside.forEach((t, i) => {
      const a = (i / Math.max(n, 1)) * Math.PI * 2;
      const r = n === 1 ? 0 : n <= 5 ? 0.3 : 0.42;
      const to = new THREE.Vector3(Math.cos(a) * r, 0.2 + (i % 2) * 0.16, Math.sin(a) * r);
      const from = t.position.clone();
      tween(0.3, (k) => t.position.lerpVectors(from, to, k));
    });
  }

  private compute(): void {
    const cube = this.store.cube;
    this.engine.clear(this.card);
    const infos = this.inside.map((t) => tokenOf(t)!);
    if (!infos.length) {
      const t = makeLabel('THE BASKET', { h: 0.2, weight: '800', color: '#ffd58a', px: 80 });
      const how = makeLabel('Throw balls in here and it answers.\nTry: Revenue + Europe + Asia Pacific', { h: 0.115, weight: '600', color: '#e6eeff', px: 60 });
      const back = panel(Math.max(t.userData.w, how.userData.w) + 0.3, 0.75, { fill: 'rgba(18,24,60,0.9)' });
      back.position.set(0, 0.42, -0.01);
      t.position.y = 0.62;
      how.position.y = 0.3;
      this.card.add(back, t, how);
      return;
    }
    const measures = infos.filter((i) => i.kind === 'measure').map((i) => i.measure!);
    const useM: MeasureKey[] = measures.length ? measures : ['revenue'];
    const key = useM[0];
    const m = MEASURES[key];
    const share = infos.some((i) => i.op === 'share');
    const yoy = infos.some((i) => i.op === 'yoy');
    const byDim = new Map<Dim, TokenInfo[]>();
    for (const i of infos) if (i.kind === 'member') byDim.set(i.dim!, [...(byDim.get(i.dim!) ?? []), i]);
    let compare: Dim | undefined;
    const base: Filter = {};
    for (const [d, vals] of byDim) {
      if (vals.length >= 2 && !compare) compare = d;
      else base[d] = vals[0].value!;
    }
    const additive = key === 'revenue' || key === 'orders' || key === 'units' || key === 'margin';
    const noteFor = (f: Filter, v: number): string | undefined => {
      if (yoy) {
        const y = cube.yoy(f, key);
        if (isFinite(y.pct)) return `${fmtPct(y.pct, true)} vs last year`;
      }
      if (share && additive) {
        const all = cube.measure(key, {});
        if (all) return `${fmtPct(v / all)} of the total`;
      }
      return undefined;
    };
    const others = (f: Filter) => useM.slice(1).map((k) => `${MEASURES[k].label} ${MEASURES[k].fmt(cube.measure(k, f))}`).join('   ·   ');
    const scope = filterText(base) + (measures.length ? '' : ' · no measure cube yet, showing Revenue');

    if (compare) {
      const members = byDim.get(compare)!;
      const items: BarItem[] = members.map((t) => {
        const f = { ...base, [compare!]: t.value! };
        const v = cube.measure(key, f);
        return { label: t.label, value: v, color: t.color, note: noteFor(f, v) };
      });
      const w = Math.max(3.4, items.length * 1.05);
      const body = bigBars(items, m.fmt, w - 0.7, 1.35);
      const H = 3.15;
      body.position.y = -H / 2 + 0.55;
      const card = answerCard(`${m.label} by ${DIM_LABEL[compare].toLowerCase()}`, body, w, H, scope);
      if (items.length === 2 && items[1].value) {
        const d = (items[0].value - items[1].value) / items[1].value;
        const c = chip(`${items[0].label} is ${fmtPct(Math.abs(d))} ${d >= 0 ? 'above' : 'below'} ${items[1].label}`, d >= 0, 0.15);
        c.position.set(0, H / 2 - 0.72, 0.02);
        card.add(c);
      }
      card.position.y = H / 2 + 0.05;
      this.card.add(card);
    } else {
      const v = cube.measure(key, base);
      const body = new THREE.Group();
      const big = makeLabel(m.fmt(v), { h: 0.55, weight: '800', px: 128 });
      big.position.y = 0.55;
      body.add(big);
      const note = noteFor(base, v);
      const g = growthChip(cube, base, key, 0.16);
      if (g) {
        g.position.set(0, 0.08, 0.02);
        body.add(g);
      }
      if (note && !yoy) {
        const n = chip(note, null, 0.14);
        n.position.set(0, -0.14, 0.02);
        body.add(n);
      }
      const extra = others(base);
      if (extra) {
        const e = makeLabel(extra, { h: 0.12, weight: '600', color: '#c5d3f5', px: 60 });
        e.position.set(0, -0.36, 0.02);
        body.add(e);
      }
      const strip = yearStrip(cube, base, key, 3.0, 0.62);
      strip.position.y = -1.42;
      body.add(strip);
      const H = 3.35;
      body.position.y = 0.05;
      const card = answerCard(m.label, body, 3.7, H, scope);
      card.position.y = H / 2 + 0.05;
      this.card.add(card);
    }
  }
}

// ------------------------------------------------------------------------------------------ the scales

export class Scales {
  readonly group = new THREE.Group();
  private beam = new THREE.Group();
  private pans: THREE.Group[] = [];
  private rings: THREE.Mesh[] = [];
  private on: (THREE.Object3D | null)[] = [null, null];
  private measureToken: THREE.Object3D | null = null;
  private card = new THREE.Group();
  private tilt = 0;
  private tiltTarget = 0;
  private readonly arm = 1.25;
  private readonly top = 2.0;

  constructor(
    private engine: Engine,
    private store: Store,
    private shelf: Shelf
  ) {
    this.group.add(pedestal(0.42, 0.3));
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.1, this.top - 0.3, 14), mat(0xe8ecf8));
    post.position.y = 0.3 + (this.top - 0.3) / 2;
    const knob = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 12), mat(0xffd58a));
    knob.position.y = this.top + 0.04;
    this.group.add(post, knob);
    this.beam.position.y = this.top;
    const bar = new THREE.Mesh(softBox(this.arm * 2 + 0.1, 0.09, 0.11, 0.04).translate(0, -0.045, 0), mat(0xe8ecf8));
    this.beam.add(bar);
    this.group.add(this.beam);

    for (const side of [-1, 1]) {
      const pan = new THREE.Group();
      const dishPts = [new THREE.Vector2(0, 0), new THREE.Vector2(0.36, 0.01), new THREE.Vector2(0.5, 0.1), new THREE.Vector2(0.46, 0.12), new THREE.Vector2(0.34, 0.05), new THREE.Vector2(0, 0.04)];
      const dish = new THREE.Mesh(new THREE.LatheGeometry(dishPts, 28), mat(0xf2c078, { side: THREE.DoubleSide }));
      for (const a of [0, 2.1, 4.2]) {
        const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.75, 6), mat(0xe8ecf8));
        cord.position.set(Math.cos(a) * 0.22, 0.44, Math.sin(a) * 0.22);
        cord.rotation.set(Math.sin(a) * 0.32, 0, -Math.cos(a) * 0.32);
        pan.add(cord);
      }
      const ring = catchRing(0.56);
      ring.position.y = 0.2;
      pan.add(dish, ring);
      this.group.add(pan);
      this.pans.push(pan);
      this.rings.push(ring);
      const idx = side < 0 ? 0 : 1;
      engine.zones.push({
        center: () => pan.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.15, 0)),
        radius: 0.6,
        accepts: (o) => tokenOf(o)?.kind === 'member',
        drop: (o) => this.put(idx, o),
        highlight: (on) => (ring.visible = on),
      });
    }
    const topRing = catchRing(0.3);
    topRing.position.y = this.top + 0.3;
    this.group.add(topRing);
    engine.zones.push({
      center: () => knob.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.25, 0)),
      radius: 0.36,
      accepts: (o) => tokenOf(o)?.kind === 'measure',
      drop: (o) => this.putMeasure(o),
      highlight: (on) => (topRing.visible = on),
    });

    const holder = new THREE.Group();
    holder.position.y = this.top + 0.75;
    holder.add(this.card);
    engine.billboards.add(holder);
    this.group.add(holder);

    store.subscribe(() => this.compute());
    engine.frame.push((dt) => this.update(dt));
    this.compute();
  }

  private put(i: number, t: THREE.Object3D): void {
    const old = this.on[i];
    if (old && old !== t) this.shelf.sendHome(old);
    tokenOf(t)!.holder = this;
    this.on[i] = t;
    this.pans[i].attach(t);
    const from = t.position.clone();
    tween(0.25, (k) => t.position.lerpVectors(from, new THREE.Vector3(0, 0.2, 0), k));
    this.compute();
  }

  private putMeasure(t: THREE.Object3D): void {
    if (this.measureToken && this.measureToken !== t) this.shelf.sendHome(this.measureToken);
    tokenOf(t)!.holder = this;
    this.measureToken = t;
    this.group.attach(t);
    const from = t.position.clone();
    tween(0.25, (k) => t.position.lerpVectors(from, new THREE.Vector3(0, this.top + 0.32, 0), k));
    this.compute();
  }

  remove(t: THREE.Object3D): void {
    this.on = this.on.map((x) => (x === t ? null : x));
    if (this.measureToken === t) this.measureToken = null;
    this.compute();
  }

  private compute(): void {
    const cube = this.store.cube;
    this.engine.clear(this.card);
    const key: MeasureKey = this.measureToken ? tokenOf(this.measureToken)!.measure! : 'revenue';
    const m = MEASURES[key];
    const sides = this.on.map((t) => {
      if (!t) return null;
      const info = tokenOf(t)!;
      return { info, value: cube.measure(key, { ...this.store.filter, [info.dim!]: info.value! }) };
    });
    const [l, r] = sides;
    if (l && r && Math.max(l.value, r.value) > 0) {
      this.tiltTarget = ((r.value - l.value) / Math.max(l.value, r.value)) * 0.36;
      const body = bigBars(
        [l, r].map((s) => ({ label: s.info.label, value: s.value, color: s.info.color })),
        m.fmt,
        2.3,
        1.1
      );
      const H = 2.85;
      body.position.y = -H / 2 + 0.55;
      const card = answerCard(`Weighing ${m.label.toLowerCase()}`, body, 3.3, H, filterText(this.store.filter));
      const hi = l.value >= r.value ? l : r;
      const lo = l.value >= r.value ? r : l;
      if (lo.value > 0) {
        const c = chip(`${hi.info.label} is ${(hi.value / lo.value).toFixed(2)}x ${lo.info.label}`, true, 0.15);
        c.position.set(0, H / 2 - 0.72, 0.02);
        card.add(c);
      }
      card.position.y = H / 2;
      this.card.add(card);
    } else {
      this.tiltTarget = l ? -0.3 : r ? 0.3 : 0;
      const t = makeLabel('THE SCALES', { h: 0.2, weight: '800', color: '#ffd58a', px: 80 });
      const how = makeLabel(
        l || r ? 'Now put a ball on the other pan.' : 'Put one ball on each pan: it weighs them.\nA measure cube on the top knob changes what is weighed.',
        { h: 0.115, weight: '600', color: '#e6eeff', px: 60 }
      );
      const back = panel(Math.max(t.userData.w, how.userData.w) + 0.3, 0.78, { fill: 'rgba(18,24,60,0.9)' });
      back.position.set(0, 0.42, -0.01);
      t.position.y = 0.63;
      how.position.y = 0.3;
      this.card.add(back, t, how);
    }
  }

  private update(dt: number): void {
    this.tilt += (this.tiltTarget - this.tilt) * Math.min(1, dt * 2.5);
    this.beam.rotation.z = -this.tilt;
    this.pans.forEach((p, i) => {
      const side = i === 0 ? -1 : 1;
      p.position.set(side * this.arm * Math.cos(this.tilt), this.top - side * this.arm * Math.sin(this.tilt) - 0.78, 0);
    });
  }
}

// ------------------------------------------------------------------------------------------ the loaf

const LEVELS: Dim[] = ['region', 'category', 'product'];

export class Slicer {
  readonly group = new THREE.Group();
  private pieces = new THREE.Group();
  private fx = new THREE.Group();
  private path: { dim: Dim; value: string | number }[] = [];
  private cut = false;
  private title: THREE.Mesh;
  private how: THREE.Mesh;
  private buttons = new THREE.Group();
  private busy = false;
  private readonly WIDTH = 3.4;
  private readonly HGT = 0.95;
  private readonly DEPTH = 0.6;
  private readonly tableY = 0.95;

  constructor(
    private engine: Engine,
    private store: Store
  ) {
    const table = new THREE.Mesh(softBox(4.0, 0.12, 1.05, 0.05), mat(STEEL));
    table.position.y = this.tableY - 0.12;
    this.group.add(pedestal(0.5, this.tableY - 0.12), table, this.pieces, this.fx, this.buttons);
    this.pieces.position.y = this.tableY;
    this.fx.position.y = this.tableY;

    const holder = new THREE.Group();
    this.title = makeLabel('CUT IT', { h: 0.2, weight: '800', color: '#ffd58a', px: 80 });
    this.how = makeLabel(' ', { h: 0.115, weight: '600', color: '#e6eeff', px: 60 });
    holder.add(this.title, this.how);
    holder.position.y = 3.25;
    engine.billboards.add(holder);
    this.group.add(holder);
    this.buttons.position.set(0, 0.5, 0.62);

    store.subscribe(() => this.render());
    this.render();
  }

  private ctx(): Filter {
    const f: Filter = {};
    if (this.store.filter.year !== undefined) f.year = this.store.filter.year;
    if (this.store.filter.month !== undefined) f.month = this.store.filter.month;
    for (const p of this.path) f[p.dim] = p.value;
    return f;
  }

  private up(): void {
    if (this.cut && this.path.length === 0) this.cut = false;
    else if (this.path.length) this.path.pop();
    this.render();
  }

  /** The cut itself: blades come down through the block, then the pieces spring apart. */
  private slice(piece?: { dim: Dim; value: string | number }): void {
    if (this.busy) return;
    if (!this.cut) this.cut = true;
    else if (piece && this.path.length < LEVELS.length - 1) this.path.push(piece);
    else return;
    this.render(true);
  }

  render(animate = false): void {
    const { engine, store, WIDTH, HGT, DEPTH } = this;
    const cube = store.cube;
    const m = MEASURES[store.measure];
    engine.clear(this.pieces);
    engine.clear(this.buttons);
    const f = this.ctx();
    const total = m.of(cube.totals(f));
    const where = this.path.length ? this.path.map((p) => memberLabel(p.dim, p.value)).join(' › ') : 'All of Aurora';

    const btns: THREE.Object3D[] = [];
    if (this.cut) btns.push(button(engine, 'Put it back together', () => this.up(), { h: 0.1, plate: 0x8a4a5a }));
    const last = this.path[this.path.length - 1];
    if (last) {
      const on = store.filter[last.dim] === last.value;
      btns.push(button(engine, on ? `Stop filtering by ${memberLabel(last.dim, last.value)}` : `Filter the whole room by ${memberLabel(last.dim, last.value)}`, () => store.toggle(last.dim, last.value), { h: 0.1, plate: 0x1f7a5f }));
    }
    if (btns.length) this.buttons.add(row(btns, 0.12));

    setLabel(this.title, `CUT IT · ${where} · ${m.fmt(total)}`);

    if (!this.cut) {
      setLabel(this.how, 'Point at the block and pull the TRIGGER to cut it.\n(Swinging the controller through it cuts too.)');
      this.how.position.y = -0.2 - this.how.userData.hgt / 2;
      const block = new THREE.Mesh(softBox(WIDTH, HGT, DEPTH, 0.09), mat(0x2f8bff));
      engine.register(block, {
        tip: 'Pull the trigger to cut',
        slice: () => this.slice(),
        hover: (on) => block.scale.setScalar(on ? 1.03 : 1),
      });
      this.pieces.add(block);
      return;
    }

    const dim = LEVELS[this.path.length];
    const rows = cube.by(dim, f).filter((r) => m.of(r.totals) > 0);
    const sum = rows.reduce((s, r) => s + m.of(r.totals), 0) || 1;
    const deeper = this.path.length < LEVELS.length - 1;
    setLabel(this.how, deeper ? `Cut by ${DIM_LABEL[dim].toLowerCase()}. Pull the TRIGGER on a piece to cut it again.` : `Cut by ${DIM_LABEL[dim].toLowerCase()}: the smallest pieces. TRIGGER on one filters the room.`);
    this.how.position.y = -0.2 - this.how.userData.hgt / 2;

    const gap = 0.12;
    const usable = WIDTH - gap * (rows.length - 1);
    let x = -WIDTH / 2;
    const selected = store.filter[dim];
    const made: { piece: THREE.Mesh; lab: THREE.Mesh; cx: number; closed: number }[] = [];
    rows.forEach((r, i) => {
      const v = m.of(r.totals);
      const w = Math.max((v / sum) * usable, 0.08);
      const cat = dim === 'product' ? cube.products.find((p) => p.product === r.key)?.category : undefined;
      const color = cat ? (CATEGORY_COLORS[cat] ?? colorOf(dim, r.key, i)) : colorOf(dim, r.key, i);
      const piece = new THREE.Mesh(softBox(w, HGT, DEPTH, Math.min(0.07, w * 0.3)), mat(color, { opacity: selected !== undefined && selected !== r.key ? 0.35 : 1 }));
      const cx = x + w / 2;
      const closed = cx - gap * i + (gap * (rows.length - 1)) / 2;
      piece.position.set(animate ? closed : cx, 0, 0);
      x += w + gap;
      const name = memberLabel(dim, r.key);
      const act = deeper ? () => this.slice({ dim, value: r.key }) : () => store.toggle(dim, r.key);
      engine.register(piece, {
        tip: `${name} · ${m.fmt(v)} · ${fmtPct(v / sum)}${deeper ? ' · trigger = cut again' : ' · trigger = filter the room'}`,
        slice: act,
        enter: () => engine.fade(() => store.enter(dim, r.key)),
        hover: (on) => piece.scale.set(1, on ? 1.1 : 1, on ? 1.1 : 1),
      });
      this.pieces.add(piece);
      const lab = makeLabel(`${w > 0.55 ? name : twoLines(name)}\n${m.fmt(v)} · ${fmtPct(v / sum)}`, { h: 0.12, px: 60, weight: '700' });
      lab.position.set(cx, HGT + 0.12 + lab.userData.hgt / 2 + (rows.length > 4 && i % 2 ? 0.42 : 0), 0);
      lab.visible = !animate;
      this.pieces.add(lab);
      made.push({ piece, lab, cx, closed });
    });

    if (!animate) return;
    // blades fall through the block at every cut line, then the pieces spring apart
    this.busy = true;
    engine.clear(this.fx);
    const blades: THREE.Mesh[] = [];
    for (let i = 0; i < made.length - 1; i++) {
      const edge = (made[i].closed + made[i + 1].closed) / 2;
      const blade = new THREE.Mesh(
        new THREE.PlaneGeometry(DEPTH + 0.5, 1.7),
        new THREE.MeshBasicMaterial({ color: 0xe0f7ff, transparent: true, opacity: 0.95, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending })
      );
      blade.rotation.y = Math.PI / 2;
      blade.position.set(edge, 2.6, 0);
      const halo = glow(1.6, 0x9be7ff, 0.9);
      halo.rotation.y = Math.PI / 2;
      blade.add(halo);
      this.fx.add(blade);
      blades.push(blade);
    }
    tween(
      0.32,
      (k) => blades.forEach((b, i) => (b.position.y = THREE.MathUtils.lerp(2.6, HGT * 0.5, Math.min(1, k * (1 + i * 0.12))))),
      () => {
        tween(0.3, (k) => blades.forEach((b) => ((b.material as THREE.MeshBasicMaterial).opacity = 0.95 * (1 - k))), () => engine.clear(this.fx));
        tween(
          0.55,
          (k) => made.forEach((p) => (p.piece.position.x = THREE.MathUtils.lerp(p.closed, p.cx, k))),
          () => {
            made.forEach((p) => (p.lab.visible = true));
            this.busy = false;
          },
          easeBack
        );
      },
      (x) => x * x
    );
  }
}
