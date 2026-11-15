// The parts that talk to the viewer: the welcome board with the controls, the clay guide and his
// "ask the data agent" keyboard, and the menu.

import * as THREE from 'three';

import { filterText, fmtPct, MEASURES, memberLabel, type Dim } from './data';
import type { Engine } from './engine';
import type { Store } from './store';
import { makeLabel, setLabel } from './text';
import { button, glow, mat, neonRing, panel, row, tween, NEON, STEEL, type Button } from './ui';

/** Asks the Fabric data agent; resolves with its answer in plain text. */
export type AskAgent = (question: string) => Promise<string>;

function wrap(text: string, width: number): string {
  const out: string[] = [];
  for (const line of text.split('\n')) {
    let cur = '';
    for (const w of line.split(' ')) {
      if (cur && (cur + ' ' + w).length > width) {
        out.push(cur);
        cur = w;
      } else cur = cur ? cur + ' ' + w : w;
    }
    out.push(cur);
  }
  return out.join('\n');
}

/** Turns the agent's markdown (tables, bold, headings) into plain short lines that read well in a speech bubble. */
export function tidyAnswer(md: string): string {
  const out: string[] = [];
  for (const raw of md.split(/\r?\n/)) {
    let line = raw.trim();
    if (/^\|?[\s:|-]+\|?$/.test(line) && line.includes('-')) continue; // the dashes under a table header
    if (line.startsWith('|')) {
      const cells = line
        .split('|')
        .map((c) => c.trim())
        .filter(Boolean);
      line = cells.length > 1 ? `${cells[0]}: ${cells.slice(1).join(' · ')}` : (cells[0] ?? '');
    }
    line = line.replace(/\*\*|__|`/g, '').replace(/^#+\s*/, '').replace(/^[-*]\s+/, '• ');
    if (line || (out.length && out[out.length - 1])) out.push(line);
  }
  return out.join('\n').trim();
}

/** Puts a panel in front of the viewer, facing them. */
function inFront(engine: Engine, g: THREE.Object3D, dist: number, y?: number): void {
  const head = engine.headPosition();
  const dir = new THREE.Vector3(0, 0, -1).applyQuaternion(engine.camera.getWorldQuaternion(new THREE.Quaternion()));
  dir.y = 0;
  dir.normalize();
  g.position.copy(head).addScaledVector(dir, dist);
  g.position.y = y ?? Math.max(1.45, head.y - 0.05);
  g.rotation.set(0, Math.atan2(-dir.x, -dir.z), 0);
}

// ------------------------------------------------------------------------------------- welcome

/** The first thing the viewer sees: what this is and what every button on the controllers does. */
export class Welcome {
  readonly group = new THREE.Group();

  constructor(
    private engine: Engine,
    source: string
  ) {
    const W = 5.4;
    const H = 4.1;
    const back = panel(W, H, { fill: 'rgba(20,28,72,0.96)' });
    back.position.z = -0.03;
    this.group.add(back);
    engine.register(back, {}); // nothing behind the board can be picked by mistake
    const title = makeLabel('AURORA · IN VR', { h: 0.36, weight: '800', px: 104 });
    title.position.y = H / 2 - 0.36;
    const sub = makeLabel(source, { h: 0.14, weight: '600', color: '#9fe3d6', px: 64 });
    sub.position.y = H / 2 - 0.72;
    this.group.add(title, sub);

    const lines: [string, string][] = [
      ['LEFT STICK', 'Glide slowly. No jumps.'],
      ['RIGHT STICK', 'Turn slowly'],
      ['TRIGGER', 'Pick, press, cut and filter: whatever you point at'],
      ['GRIP', 'Grab. A ball flies to your hand: point at the basket, let go'],
      ['A  or  X', 'Go inside what you point at. Pointing at nothing: the menu'],
      ['B  or  Y', 'One step back'],
      ['PC', 'Click, hold right button to grab, W A S D, Q E, F, B, M'],
    ];
    lines.forEach(([key, what], i) => {
      const y = H / 2 - 1.12 - i * 0.33;
      const k = makeLabel(key, { h: 0.15, weight: '800', px: 72, color: '#0b1020', bg: '#ffd58a' });
      k.position.set(-W / 2 + 0.3 + k.userData.w / 2, y, 0);
      const t = makeLabel(what, { h: 0.14, weight: '600', px: 64, color: '#e6eeff' });
      t.position.set(-W / 2 + 1.75 + t.userData.w / 2, y, 0);
      this.group.add(k, t);
    });
    const tip = makeLabel('Every station has a sign that says what to do. The words on the floor point to them.', { h: 0.12, weight: '600', px: 60, color: '#a9bdf0' });
    tip.position.y = -H / 2 + 0.78;
    const start = button(engine, 'START', () => this.show(false), { h: 0.22, plate: 0x1fa88f, minW: 1.6 });
    start.position.set(0, -H / 2 + 0.36, 0.05);
    this.group.add(tip, start);
    this.group.position.set(0, 2.25, -3.7);
  }

  show(on: boolean): void {
    if (on) {
      this.group.visible = true;
      inFront(this.engine, this.group, 3.7, 2.25);
      tween(0.35, (k) => this.group.scale.setScalar(0.6 + 0.4 * k));
    } else {
      tween(0.3, (k) => this.group.scale.setScalar(1 - 0.5 * k), () => (this.group.visible = false));
    }
  }
}

// ------------------------------------------------------------------------------------- the clay guide

/** Clay Shai stands near the viewer, answers a few quick questions from the loaded data, and passes any other question to the Fabric data agent. */
export class Guide {
  readonly group = new THREE.Group();
  private bubble: THREE.Mesh;
  private readonly h = 1.85;

  constructor(
    engine: Engine,
    private store: Store,
    private openAsk: () => void
  ) {
    const holder = new THREE.Group();
    const h = this.h;
    // The guide is his real photo (the one on his site), with a see-through blue cast as on the site: he
    // belongs to the room's light, and a little of what is behind him shows through.
    // Slightly see-through, but it still writes depth: lights of the deck behind him are hidden, solid things show a little.
    const spriteMat = new THREE.MeshBasicMaterial({ alphaTest: 0.45, transparent: true, opacity: 0.86, depthWrite: true });
    new THREE.ImageLoader().load('./guide.png', (img) => {
      const c = document.createElement('canvas');
      c.width = img.width;
      c.height = img.height;
      const x = c.getContext('2d')!;
      x.drawImage(img, 0, 0);
      const d = x.getImageData(0, 0, c.width, c.height);
      const p = d.data;
      for (let y = 0; y < c.height; y++) {
        const line = 1;
        for (let i = y * c.width * 4, end = i + c.width * 4; i < end; i += 4) {
          const l = (p[i] * 0.3 + p[i + 1] * 0.59 + p[i + 2] * 0.11) / 255;
          // keep a little over half of his own colours, the rest is cool light
          // a blue filter over the whole picture; the black shirt becomes deep navy instead of melting into the sky
          p[i] = (p[i] * 0.56 + (18 + 70 * l) * 0.44) * line;
          p[i + 1] = (p[i + 1] * 0.62 + (96 + 115 * l) * 0.38) * line;
          p[i + 2] = Math.min(255, (p[i + 2] * 0.56 + (205 + 50 * l) * 0.44) * line);
        }
      }
      x.putImageData(d, 0, 0);
      const tex = new THREE.CanvasTexture(c);
      tex.colorSpace = THREE.SRGBColorSpace;
      spriteMat.map = tex;
      spriteMat.needsUpdate = true;
    });
    const sprite = new THREE.Mesh(new THREE.PlaneGeometry((h * 580) / 860, h), spriteMat);
    sprite.position.y = h / 2 + 0.1;
    const halo = glow(3.4, 0x6fd0ff, 0.5);
    halo.position.set(0, h / 2 + 0.15, -0.06);
    const pool = glow(2.6, NEON, 0.7, true);
    pool.position.y = 0.02;
    // the projector he stands on: a dark disc, two rings of light and a cone of light rising from it
    const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.85, 0.1, 40), mat(STEEL));
    stand.position.y = 0.05;
    const ringA = neonRing(0.78, NEON, 0.016);
    ringA.position.y = 0.105;
    const ringB = neonRing(0.5, NEON, 0.01);
    ringB.position.y = 0.105;
    const beamCanvas = document.createElement('canvas');
    beamCanvas.width = 8;
    beamCanvas.height = 128;
    const bx = beamCanvas.getContext('2d')!;
    const bg = bx.createLinearGradient(0, 0, 0, 128);
    bg.addColorStop(0, 'rgba(255,255,255,0)');
    bg.addColorStop(1, 'rgba(255,255,255,0.55)');
    bx.fillStyle = bg;
    bx.fillRect(0, 0, 8, 128);
    const beam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.62, 0.48, 1.0, 40, 1, true),
      new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(beamCanvas), color: NEON, transparent: true, opacity: 0.5, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending })
    );
    beam.position.y = 0.6;
    this.group.add(pool, stand, ringA, ringB, beam);
    this.bubble = makeLabel(' ', { h: 0.115, bg: 'rgba(6,14,36,0.95)', edge: 'rgba(96,222,255,0.95)', color: '#eaf8ff', px: 64, weight: '700' });
    holder.add(halo, sprite, this.bubble);
    engine.billboards.add(holder);
    this.group.add(holder);
    engine.frame.push((_dt, t) => (sprite.position.y = h / 2 + 0.1 + Math.sin(t * 1.2) * 0.025));

    const quick = (text: string, fn: () => string) => button(engine, text, () => this.say(fn()), { h: 0.105, px: 60, plate: 0x4a3f8a, minW: 2.0 });
    const qs: THREE.Object3D[] = [
      button(engine, 'ASK THE DATA AGENT', () => this.openAsk(), { h: 0.14, px: 72, plate: 0x1fa88f, minW: 2.0, tip: 'Type or say any question; the Fabric data agent answers' }),
      quick('Where should I look?', () => this.whereToLook()),
      quick('Which region grew most?', () => this.bestGrowth()),
      quick('What is the top product?', () => this.topProduct()),
      quick('Which month was weakest?', () => this.weakestMonth()),
    ];
    const side = new THREE.Group();
    let y = 1.75;
    for (const q of qs) {
      q.position.set(0, y - q.userData.h / 2, 0);
      y -= q.userData.h + 0.07;
      side.add(q);
    }
    side.position.set(-1.9, 0, 0.15); // on his far side, away from the boards
    side.rotation.y = 0.4;
    this.group.add(side);
    this.say('Hi, I am Shai. These are the real Aurora numbers.\nPoint at anything and pull the trigger.\nOr ask me a question.');
  }

  say(text: string, max = 620): void {
    const t = text.length > max ? text.slice(0, max - 20).trimEnd() + ' …' : text;
    setLabel(this.bubble, wrap(t, max > 620 ? 62 : 44));
    this.bubble.position.y = this.h + 0.4 + this.bubble.userData.hgt / 2;
  }

  private whereToLook(): string {
    const { cube, measure } = this.store;
    let worst = { name: '', pct: Infinity, dim: 'region' as Dim, key: '' as string | number };
    for (const d of ['region', 'category'] as Dim[]) {
      for (const k of cube.members(d)) {
        const y = cube.yoy({ [d]: k }, measure);
        if (isFinite(y.pct) && y.pct < worst.pct) worst = { name: String(k), pct: y.pct, dim: d, key: k };
      }
    }
    if (!worst.name) return 'Nothing to compare yet.';
    this.store.set(worst.dim, worst.key);
    return `Look at ${worst.name}: ${fmtPct(worst.pct, true)} against last year, the slowest of all.\nI filtered the room by it. B or Y takes you back.`;
  }
  private bestGrowth(): string {
    const { cube, measure } = this.store;
    const rows = cube.regions.map((r) => ({ r, y: cube.yoy({ region: r }, measure) })).filter((x) => isFinite(x.y.pct));
    rows.sort((a, b) => b.y.pct - a.y.pct);
    if (!rows.length) return 'Nothing to compare yet.';
    return rows.map((x, i) => `${i + 1}. ${x.r}: ${fmtPct(x.y.pct, true)}`).join('\n') + `\n${cube.latestYear} so far against the same months of ${cube.latestYear - 1}`;
  }
  private topProduct(): string {
    const { cube, measure, filter } = this.store;
    const m = MEASURES[measure];
    const rows = cube.by('product', filter).sort((a, b) => m.of(b.totals) - m.of(a.totals));
    const sum = rows.reduce((s, r) => s + m.of(r.totals), 0) || 1;
    return `${filterText(filter)}:\n` + rows.slice(0, 3).map((r, i) => `${i + 1}. ${r.key}: ${m.fmt(m.of(r.totals))} (${fmtPct(m.of(r.totals) / sum)})`).join('\n');
  }
  private weakestMonth(): string {
    const { cube, measure, filter } = this.store;
    const m = MEASURES[measure];
    const year = (filter.year as number | undefined) ?? cube.latestYear;
    const rows = cube.by('month', { ...filter, year }).filter((r) => m.of(r.totals) > 0);
    rows.sort((a, b) => m.of(a.totals) - m.of(b.totals));
    if (!rows.length) return 'No months with data here.';
    return `${memberLabel('month', rows[0].key)} ${year} was the weakest: ${m.fmt(m.of(rows[0].totals))}.\nThe strongest was ${memberLabel('month', rows[rows.length - 1].key)}: ${m.fmt(m.of(rows[rows.length - 1].totals))}.`;
  }
}

// ------------------------------------------------------------------------------------- ask panel

type SpeechCtor = new () => {
  lang: string;
  interimResults: boolean;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
};

/** A keyboard in the air for a question to the data agent. Also takes the headset's own keyboard (with its microphone key) and, where the browser has it, speech. */
export class AskPanel {
  readonly group = new THREE.Group();
  private text = '';
  private line: THREE.Mesh;
  private status: THREE.Mesh;
  private input: HTMLInputElement;

  constructor(
    private engine: Engine,
    private guide: Guide,
    private ask: AskAgent | undefined
  ) {
    const W = 4.6;
    const H = 3.5;
    const back = panel(W, H, { fill: 'rgba(16,22,58,0.97)' });
    back.position.z = -0.04;
    this.group.add(back);
    engine.register(back, {});
    const title = makeLabel('ASK THE DATA AGENT', { h: 0.2, weight: '800', color: '#9fe3d6', px: 80 });
    title.position.y = H / 2 - 0.26;
    this.line = makeLabel(' ', { h: 0.15, weight: '700', px: 68, color: '#0b1020', bg: '#f8fafc' });
    this.line.position.y = H / 2 - 0.66;
    this.status = makeLabel(' ', { h: 0.105, weight: '600', px: 56, color: '#a9bdf0' });
    this.status.position.y = H / 2 - 0.96;
    this.group.add(title, this.line, this.status);

    const key = (ch: string, label = ch, minW = 0.3) => button(engine, label, () => this.type(ch), { h: 0.14, px: 64, minW, plate: 0x33448f });
    const rows = ['1234567890', 'QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM?'];
    rows.forEach((r, i) => {
      const g = row(
        r.split('').map((c) => key(c.toLowerCase(), c)),
        0.05
      );
      g.position.y = H / 2 - 1.3 - i * 0.3;
      g.position.z = 0.02;
      this.group.add(g);
    });
    const bottom = row(
      [
        button(engine, 'space', () => this.type(' '), { h: 0.14, px: 64, minW: 1.3, plate: 0x33448f }),
        button(engine, 'delete', () => this.set(this.text.slice(0, -1)), { h: 0.14, px: 64, plate: 0x8a4a5a }),
        button(engine, 'clear', () => this.set(''), { h: 0.14, px: 64, plate: 0x8a4a5a }),
        button(engine, 'ASK', () => this.send(), { h: 0.16, px: 72, plate: 0x1fa88f, minW: 0.8 }),
      ],
      0.1
    );
    bottom.position.set(0, H / 2 - 2.52, 0.02);
    this.group.add(bottom);

    const extra: THREE.Object3D[] = [
      button(engine, 'Headset keyboard / microphone', () => this.systemKeyboard(), { h: 0.11, px: 56, plate: 0x4a3f8a, tip: 'Opens the headset keyboard. Its microphone key turns speech into text' }),
    ];
    if (this.speech()) extra.push(button(engine, 'Speak', () => this.listen(), { h: 0.11, px: 56, plate: 0x4a3f8a }));
    extra.push(button(engine, 'Close', () => this.show(false), { h: 0.11, px: 56 }));
    const er = row(extra, 0.1);
    er.position.set(0, H / 2 - 2.9, 0.02);
    this.group.add(er);
    const eg = row(
      ['Which region grew most this year?', 'Top 3 products in 2026'].map((q) => button(engine, q, () => this.set(q), { h: 0.095, px: 52, plate: 0x26356f })),
      0.1
    );
    eg.position.set(0, H / 2 - 3.24, 0.02);
    this.group.add(eg);

    // a real text field, off screen: it is what the headset keyboard (and a PC keyboard) types into
    this.input = document.createElement('input');
    this.input.type = 'text';
    this.input.setAttribute('aria-label', 'Question for the data agent');
    Object.assign(this.input.style, { position: 'fixed', left: '-2000px', top: '0', opacity: '0' });
    document.body.appendChild(this.input);
    this.input.addEventListener('input', () => this.set(this.input.value, false));
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.send();
    });
    this.group.visible = false;
    this.set('');
  }

  private speech(): SpeechCtor | undefined {
    const w = window as unknown as { SpeechRecognition?: SpeechCtor; webkitSpeechRecognition?: SpeechCtor };
    return w.SpeechRecognition ?? w.webkitSpeechRecognition;
  }

  show(on = !this.group.visible): void {
    this.group.visible = on;
    if (!on) {
      this.input.blur();
      return;
    }
    inFront(this.engine, this.group, 3.0, 1.95);
    setLabel(this.status, this.ask ? 'Type with the pointer, or use the headset keyboard. Then press ASK.' : 'The data agent is not connected in this build.');
    if (!this.engine.presenting) this.input.focus();
  }

  private set(t: string, sync = true): void {
    this.text = t.slice(0, 160);
    if (sync) this.input.value = this.text;
    setLabel(this.line, wrap(this.text || 'Your question…', 52));
  }

  private type(ch: string): void {
    this.set(this.text + ch);
  }

  /** Focusing a real text field opens the headset's own keyboard, which also has a microphone key. */
  private systemKeyboard(): void {
    const session = this.engine.renderer.xr.getSession() as (XRSession & { isSystemKeyboardSupported?: boolean }) | null;
    if (session && session.isSystemKeyboardSupported === false) {
      setLabel(this.status, 'This headset browser does not offer its keyboard here. Use the keys above.');
      return;
    }
    this.input.value = this.text;
    this.input.focus();
    setLabel(this.status, 'Type on the headset keyboard (its microphone key writes what you say), then press ASK.');
  }

  private listen(): void {
    const Ctor = this.speech();
    if (!Ctor) return;
    try {
      const rec = new Ctor();
      rec.lang = 'en-US';
      rec.interimResults = false;
      setLabel(this.status, 'Listening… say your question');
      rec.onresult = (e) => {
        this.set(e.results[0][0].transcript);
        setLabel(this.status, 'Got it. Press ASK, or fix it with the keys.');
      };
      rec.onerror = (e) => setLabel(this.status, `Could not listen (${e.error}). Use the keys or the headset keyboard.`);
      rec.start();
    } catch {
      setLabel(this.status, 'Speech is not available here. Use the keys or the headset keyboard.');
    }
  }

  private send(): void {
    const q = this.text.trim();
    if (q.length < 3) {
      setLabel(this.status, 'Write a question first.');
      return;
    }
    this.show(false);
    if (!this.ask) {
      this.guide.say(`You asked: ${q}\nThe data agent is not connected in this build.`);
      return;
    }
    this.guide.say(`You asked: ${q}\nAsking the Fabric data agent… this can take a minute.`);
    const started = performance.now();
    this.ask(q)
      .then((a) => this.guide.say(`${q}\n\n${tidyAnswer(a) || 'The agent gave no answer.'}\n(Fabric data agent · ${Math.round((performance.now() - started) / 1000)} s)`, 1100))
      .catch((err: unknown) => this.guide.say(`${q}\n\nThe data agent could not answer: ${err instanceof Error ? err.message : String(err)}`));
  }
}

// ------------------------------------------------------------------------------------- the menu

export interface MenuActions {
  resetRoom(): void;
  addBoard(dim: Dim): void;
  help(): void;
}

/** Opens in front of the viewer on A / X while pointing at nothing (or M): measure, year, boards, help. */
export class Menu {
  readonly group = new THREE.Group();
  private measureBtns: Record<string, Button> = {};
  private yearBtns: Record<string, Button> = {};

  constructor(
    private engine: Engine,
    private store: Store,
    actions: MenuActions
  ) {
    const W = 5.0;
    const H = 2.7;
    const back = panel(W, H, { fill: 'rgba(10,18,46,0.9)' });
    back.position.z = -0.04;
    this.group.add(back);
    engine.register(back, {});
    const title = makeLabel('MENU', { h: 0.24, weight: '800', px: 88 });
    title.position.y = H / 2 - 0.3;
    this.group.add(title);

    const line = (caption: string, y: number, items: THREE.Object3D[]) => {
      const cap = makeLabel(caption, { h: 0.12, color: '#a9bdf0', weight: '700', px: 60 });
      cap.position.set(-W / 2 + 0.25 + cap.userData.w / 2, y, 0);
      const r = row(items, 0.1);
      r.position.set(0.45, y, 0.02);
      this.group.add(cap, r);
    };
    const mb = (k: Store['measure']) => (this.measureBtns[k] = button(engine, MEASURES[k].label, () => store.setMeasure(k), { h: 0.12 }));
    line('Measure', H / 2 - 0.8, [mb('revenue'), mb('orders'), mb('units'), mb('margin')]);
    const yb = (y: number | undefined, text: string) => (this.yearBtns[String(y)] = button(engine, text, () => store.set('year', y), { h: 0.12, minW: 0.6 }));
    line('Year', H / 2 - 1.22, [yb(undefined, 'All'), ...store.cube.years.map((y) => yb(y, String(y)))]);
    line('New board', H / 2 - 1.64, (['month', 'region', 'category', 'product'] as Dim[]).map((d) => button(engine, d, () => actions.addBoard(d), { h: 0.11, px: 56 })));
    const last = row(
      [
        button(engine, 'Clear all filters', () => store.reset(), { h: 0.12, plate: 0x8a4a5a }),
        button(engine, 'Reset the room', () => actions.resetRoom(), { h: 0.12, plate: 0x8a4a5a }),
        button(engine, 'How it works', () => actions.help(), { h: 0.12, plate: 0x4a3f8a }),
        button(engine, 'Close', () => this.toggle(false), { h: 0.12 }),
      ],
      0.1
    );
    last.position.set(0, H / 2 - 2.2, 0.02);
    this.group.add(last);
    this.group.visible = false;
    store.subscribe(() => this.paint());
    this.paint();
  }

  paint(): void {
    for (const [k, b] of Object.entries(this.measureBtns)) b.setActive(k === this.store.measure);
    for (const [k, b] of Object.entries(this.yearBtns)) b.setActive(k === String(this.store.filter.year));
  }

  toggle(on = !this.group.visible): void {
    this.group.visible = on;
    if (!on) return;
    this.paint();
    inFront(this.engine, this.group, 3.0, 1.9);
  }
}
