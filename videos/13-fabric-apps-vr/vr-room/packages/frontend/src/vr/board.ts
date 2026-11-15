// The "regular" visuals: a glass board with clay columns or bars for one dimension, in big type.
// A board can be picked up (grip), turned, pushed away or pulled closer with the stick, resized with two
// hands, hung anywhere, or dropped in the bin. Trigger on a bar filters the whole room by it; A / X goes inside.

import * as THREE from 'three';

import { colorOf, CATEGORY_COLORS, DIM_LABEL, filterText, MEASURES, memberLabel, MONTHS, type Dim, type Filter } from './data';
import type { Engine } from './engine';
import type { Store } from './store';
import { anchorLabel, makeLabel } from './text';
import { mat, panel, softBox } from './ui';

const W = 3.4;
const HEIGHT: Record<Dim, number> = { month: 2.3, region: 2.3, year: 2.3, category: 2.1, product: 3.0 };

function twoLines(s: string): string {
  if (s.length <= 9 || !s.includes(' ')) return s;
  const words = s.split(' ');
  const half = Math.ceil(words.length / 2);
  return words.slice(0, half).join(' ') + '\n' + words.slice(half).join(' ');
}

export class Board {
  readonly group = new THREE.Group();
  private content = new THREE.Group();
  readonly H: number;

  constructor(
    private engine: Engine,
    private store: Store,
    public dim: Dim,
    public id: string,
    onMoved: () => void
  ) {
    const H = (this.H = HEIGHT[dim]);
    const back = panel(W, H);
    back.position.z = -0.2;
    this.group.add(back, this.content);
    this.group.userData.board = this;
    engine.register(this.group, { grab: { scale: true, onRelease: onMoved } });
    this.render();
  }

  render(): void {
    const { engine, store, dim, H } = this;
    const cube = store.cube;
    const m = MEASURES[store.measure];
    engine.clear(this.content);
    const c = this.content;

    const ctx: Filter = { ...store.filter };
    delete ctx[dim];
    const title = makeLabel(`${m.label} by ${DIM_LABEL[dim].toLowerCase()}`, { h: 0.22, weight: '800', px: 88 });
    title.position.set(0, H / 2 - 0.24, 0);
    const total = m.of(cube.totals(store.filter));
    const sub = makeLabel(`${filterText(store.filter)} · ${m.fmt(total)}`, { h: 0.13, color: '#a9bdf0', weight: '600', px: 64 });
    sub.position.set(0, H / 2 - 0.5, 0);
    c.add(title, sub);

    const selected = store.filter[dim];
    const baseY = -H / 2 + 0.42;
    const maxH = H - 1.42;

    const addBar = (geo: THREE.BufferGeometry, key: string | number, color: number, value: number, extra: string, pos: THREE.Vector3): THREE.Mesh => {
      const dimmed = selected !== undefined && selected !== key;
      const mesh = new THREE.Mesh(geo, mat(color, { opacity: dimmed ? 0.3 : 1 }));
      mesh.position.copy(pos);
      const name = memberLabel(dim, key);
      engine.register(mesh, {
        tip: () => `${name} · ${m.fmt(value)}${extra}`,
        select: () => store.toggle(dim, key),
        enter: () => engine.fade(() => store.enter(dim, key)),
        hover: (on) => mesh.scale.setScalar(on ? 1.07 : 1),
      });
      c.add(mesh);
      return mesh;
    };

    if (dim === 'month') {
      const year = (ctx.year as number | undefined) ?? cube.latestYear;
      const other = year === cube.years[0] ? undefined : year - 1;
      const cur = cube.by('month', { ...ctx, year });
      const prev = other !== undefined ? cube.by('month', { ...ctx, year: other }) : [];
      const max = Math.max(1, ...cur.map((r) => m.of(r.totals)), ...prev.map((r) => m.of(r.totals)));
      const step = (W - 0.3) / 12;
      cur.forEach((r, i) => {
        const x = -W / 2 + 0.15 + step * (i + 0.5);
        const v = m.of(r.totals);
        const pv = prev[i] ? m.of(prev[i].totals) : 0;
        if (pv > 0) {
          const ghost = new THREE.Mesh(softBox(step * 0.5, (pv / max) * maxH, 0.07), mat(0x7f8fc8, { opacity: 0.55 }));
          ghost.position.set(x + step * 0.17, baseY, -0.09);
          c.add(ghost);
        }
        if (v > 0) {
          const hgt = Math.max((v / max) * maxH, 0.02);
          const yoy = pv > 0 ? ` · ${v >= pv ? '+' : ''}${(((v - pv) / pv) * 100).toFixed(1)}% vs ${other}` : '';
          addBar(softBox(step * 0.62, hgt, 0.16), r.key, 0x2f8bff, v, yoy, new THREE.Vector3(x, baseY, 0));
          const short = v >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : v >= 1e3 ? Math.round(v / 1e3) + 'K' : String(Math.round(v));
          const val = makeLabel(short, { h: 0.105, weight: '800', px: 56 });
          val.position.set(x, baseY + hgt + 0.085, 0.03);
          c.add(val);
        }
        const lab = makeLabel(MONTHS[i], { h: 0.11, color: '#c5d3f5', weight: '700', px: 56 });
        lab.position.set(x, baseY - 0.1, 0.03);
        c.add(lab);
      });
      const legend = makeLabel(other !== undefined ? `${year} in blue · ${other} behind it` : `${year}`, { h: 0.1, color: '#9fb4e8', weight: '500', px: 52 });
      legend.position.set(0, -H / 2 + 0.12, 0);
      c.add(legend);
    } else if (dim === 'region' || dim === 'year') {
      const rows = cube.by(dim, ctx);
      const max = Math.max(1, ...rows.map((r) => m.of(r.totals)));
      const sum = rows.reduce((s, r) => s + m.of(r.totals), 0) || 1;
      const step = (W - 0.4) / rows.length;
      const top = maxH - 0.22;
      rows.forEach((r, i) => {
        const x = -W / 2 + 0.2 + step * (i + 0.5);
        const v = m.of(r.totals);
        const hgt = Math.max((v / max) * top, 0.03);
        const w = Math.min(step * 0.56, 0.5);
        addBar(softBox(w, hgt, w * 0.8), r.key, colorOf(dim, r.key, i), v, ` · ${((v / sum) * 100).toFixed(0)}% of the total`, new THREE.Vector3(x, baseY + 0.16, 0.05));
        const val = makeLabel(m.fmt(v), { h: 0.17, weight: '800', px: 72 });
        val.position.set(x, baseY + 0.16 + hgt + 0.14, 0.06);
        const lab = makeLabel(twoLines(memberLabel(dim, r.key)), { h: 0.115, color: '#dbe6ff', weight: '700', px: 60 });
        lab.position.set(x, baseY + 0.02 - lab.userData.hgt / 2 + 0.06, 0.25);
        c.add(val, lab);
      });
    } else {
      // categories and products: horizontal bars, biggest on top
      const rows = cube.by(dim, ctx).sort((a, b) => m.of(b.totals) - m.of(a.totals));
      const max = Math.max(1, ...rows.map((r) => m.of(r.totals)));
      const sum = rows.reduce((s, r) => s + m.of(r.totals), 0) || 1;
      const top = H / 2 - 0.7;
      const rowH = Math.min(0.32, (H - 0.95) / rows.length);
      const x0 = -W / 2 + 1.5;
      const maxW = W - 2.3;
      const th = Math.min(0.115, rowH * 0.58);
      rows.forEach((r, i) => {
        const y = top - rowH * (i + 0.5);
        const v = m.of(r.totals);
        const w = Math.max((v / max) * maxW, 0.03);
        const g = softBox(w, rowH * 0.62, 0.14, rowH * 0.2);
        g.translate(w / 2, -rowH * 0.31, 0);
        const cat = dim === 'category' ? String(r.key) : (cube.products.find((p) => p.product === r.key)?.category ?? '');
        addBar(g, r.key, CATEGORY_COLORS[cat] ?? colorOf(dim, r.key, i), v, ` · ${((v / sum) * 100).toFixed(0)}% of the total`, new THREE.Vector3(x0, y, 0));
        const lab = makeLabel(String(r.key), { h: th, color: '#e6eeff', weight: '600', px: 56 });
        lab.position.set(0, y, 0.03);
        anchorLabel(lab, x0 - 0.07, 'right');
        const val = makeLabel(m.fmt(v), { h: th, weight: '800', px: 56 });
        val.position.set(0, y, 0.03);
        anchorLabel(val, x0 + w + 0.06, 'left');
        c.add(lab, val);
      });
    }
  }
}
