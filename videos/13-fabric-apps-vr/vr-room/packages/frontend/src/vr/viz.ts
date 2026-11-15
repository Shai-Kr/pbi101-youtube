// Big, readable answer visuals: tall clay columns for a comparison, a huge number with a year of months
// under it for a single answer. Used above the basket and the scales.

import * as THREE from 'three';

import { fmtPct, MEASURES, MONTHS, type Cube, type Filter, type MeasureKey } from './data';
import { makeLabel } from './text';
import { easeBack, glow, mat, panel, softBox, tween } from './ui';

export interface BarItem {
  label: string;
  value: number;
  color: number;
  /** A second, smaller line under the value (growth, share...). */
  note?: string;
}

function twoLines(s: string): string {
  if (s.length <= 9 || !s.includes(' ')) return s;
  const words = s.split(' ');
  const half = Math.ceil(words.length / 2);
  return words.slice(0, half).join(' ') + '\n' + words.slice(half).join(' ');
}

/** Tall columns side by side, growing in with a small bounce. The origin is the middle of the base line. */
export function bigBars(items: BarItem[], fmt: (v: number) => string, width = 3.2, maxH = 1.5): THREE.Group {
  const g = new THREE.Group();
  const max = Math.max(1e-9, ...items.map((i) => i.value));
  const step = width / items.length;
  const bw = Math.min(step * 0.6, 0.7);
  items.forEach((it, i) => {
    const x = -width / 2 + step * (i + 0.5);
    const h = Math.max((it.value / max) * maxH, 0.03);
    const bar = new THREE.Mesh(softBox(bw, h, bw * 0.8), mat(it.color));
    bar.position.set(x, 0, 0);
    tween(0.7 + i * 0.08, (k) => bar.scale.set(1, Math.max(k, 0.01), 1), undefined, easeBack);
    const pool = glow(bw * 3.2, it.color, 0.5, true);
    pool.position.set(x, 0.01, 0);
    const val = makeLabel(fmt(it.value), { h: 0.24, weight: '800', px: 88 });
    val.position.set(x, h + 0.2, 0.05);
    g.add(pool, bar, val);
    if (it.note) {
      const note = makeLabel(it.note, { h: 0.13, weight: '600', color: it.note.startsWith('-') ? '#fca5a5' : '#86efac', px: 60 });
      note.position.set(x, h + 0.43, 0.05);
      g.add(note);
    }
    const name = makeLabel(twoLines(it.label), { h: 0.14, weight: '700', color: '#dbe6ff', px: 64 });
    name.position.set(x, -0.1 - name.userData.hgt / 2, 0.05);
    g.add(name);
  });
  return g;
}

/** One year as twelve small columns, with last year as a paler column behind each. */
export function yearStrip(cube: Cube, f: Filter, key: MeasureKey, width = 3.2, maxH = 0.75): THREE.Group {
  const g = new THREE.Group();
  const m = MEASURES[key];
  const ctx: Filter = { ...f };
  delete ctx.month;
  const year = (ctx.year as number | undefined) ?? cube.latestYear;
  const cur = cube.by('month', { ...ctx, year });
  const prev = year > cube.years[0] ? cube.by('month', { ...ctx, year: year - 1 }) : [];
  const max = Math.max(1e-9, ...cur.map((r) => m.of(r.totals)), ...prev.map((r) => m.of(r.totals)));
  const step = width / 12;
  cur.forEach((r, i) => {
    const x = -width / 2 + step * (i + 0.5);
    const v = m.of(r.totals);
    const pv = prev[i] ? m.of(prev[i].totals) : 0;
    if (isFinite(pv) && pv > 0) {
      const ghost = new THREE.Mesh(softBox(step * 0.5, Math.max((pv / max) * maxH, 0.02), 0.08), mat(0x7f8fc8, { opacity: 0.55 }));
      ghost.position.set(x + step * 0.14, 0, -0.07);
      g.add(ghost);
    }
    if (isFinite(v) && v > 0) {
      const bar = new THREE.Mesh(softBox(step * 0.58, Math.max((v / max) * maxH, 0.02), 0.14), mat(0x2f8bff));
      bar.position.set(x, 0, 0);
      tween(0.5 + i * 0.03, (k) => bar.scale.set(1, Math.max(k, 0.01), 1), undefined, easeBack);
      g.add(bar);
    }
    const lab = makeLabel(MONTHS[i], { h: 0.1, color: '#c5d3f5', weight: '600', px: 52 });
    lab.position.set(x, -0.09, 0.03);
    g.add(lab);
  });
  const legend = makeLabel(prev.length ? `${year} in blue · ${year - 1} behind it` : String(year), { h: 0.095, color: '#9fb4e8', weight: '500', px: 52 });
  legend.position.set(0, -0.27, 0.03);
  g.add(legend);
  return g;
}

/** A framed answer card: headline, then whatever visual is passed in, on a glass panel. */
export function answerCard(title: string, body: THREE.Object3D, w: number, h: number, sub?: string): THREE.Group {
  const g = new THREE.Group();
  const back = panel(w, h, { fill: 'rgba(22,30,74,0.9)' });
  back.position.z = -0.22;
  const t = makeLabel(title, { h: 0.2, weight: '800', px: 80 });
  t.position.set(0, h / 2 - 0.24, 0);
  g.add(back, t);
  if (sub) {
    const s = makeLabel(sub, { h: 0.12, weight: '600', color: '#a9bdf0', px: 60 });
    s.position.set(0, h / 2 - 0.47, 0);
    g.add(s);
  }
  g.add(body);
  return g;
}

/** A pill with a number in it ("+32.5% vs last year"), green for up and red for down. */
export function chip(text: string, good: boolean | null, h = 0.16): THREE.Mesh {
  return makeLabel(text, {
    h,
    weight: '800',
    px: 72,
    color: '#0b1020',
    bg: good === null ? '#cbd5e1' : good ? '#6ee7b7' : '#fca5a5',
  });
}

export function growthChip(cube: Cube, f: Filter, key: MeasureKey, h = 0.16): THREE.Mesh | null {
  const y = cube.yoy(f, key);
  if (!isFinite(y.pct)) return null;
  return chip(`${fmtPct(y.pct, true)} vs last year`, y.pct >= 0, h);
}
