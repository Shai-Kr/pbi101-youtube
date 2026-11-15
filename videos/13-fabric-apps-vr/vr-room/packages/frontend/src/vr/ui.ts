// Building blocks shared by everything in the room: the glossy look, bevelled shapes, placing things on the
// circle around the viewer, holographic panels, buttons, signs, short animations.

import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

import type { Engine } from './engine';
import { makeLabel, type LabelOpts } from './text';

/** The accent light of the room (panel edges, rings, frames). */
export const NEON = 0x5fd8ff;
export const NEON_CSS = 'rgba(96,222,255,0.95)';
/** Dark metal for everything structural (pedestals, posts, tables). */
export const STEEL = 0x232c4a;

/** Position on the circle around the middle: 0 degrees is straight ahead, 90 is to the right. Faces the middle. */
export function place(obj: THREE.Object3D, angleDeg: number, r: number, y = 0): THREE.Object3D {
  const a = THREE.MathUtils.degToRad(angleDeg);
  obj.position.set(Math.sin(a) * r, y, -Math.cos(a) * r);
  obj.rotation.set(0, -a, 0);
  return obj;
}

const tweens: { t: number; dur: number; fn: (k: number) => void; done?: () => void; ease: (x: number) => number }[] = [];
const easeOut = (x: number) => 1 - Math.pow(1 - x, 3);
/** Overshoots a little and settles: for things that pop into place. */
export const easeBack = (x: number) => 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2);

/** Runs fn with k going 0 -> 1 over dur seconds. */
export function tween(dur: number, fn: (k: number) => void, done?: () => void, ease: (x: number) => number = easeOut): void {
  fn(0);
  tweens.push({ t: 0, dur, fn, done, ease });
}

export function runTweens(dt: number): void {
  for (let i = tweens.length - 1; i >= 0; i--) {
    const w = tweens[i];
    w.t += dt;
    const x = Math.min(w.t / w.dur, 1);
    w.fn(w.ease(x));
    if (x >= 1) {
      tweens.splice(i, 1);
      w.done?.();
    }
  }
}

// ------------------------------------------------------------------ the glossy look
//
// No lights in the scene (cheap on a headset). Every solid surface borrows its shading from one small picture
// of a polished ball, looked up by the direction the surface faces. The picture holds three separate things:
//   red   = how bright the body colour is (a bright sky above, a dark floor below, like a reflection)
//   green = white highlights (two studio lights), added on top of any colour
//   blue  = light on the silhouette (the neon rim)

const S = 256;

function layer(draw: (x: CanvasRenderingContext2D) => void): Uint8ClampedArray {
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const x = c.getContext('2d')!;
  x.fillStyle = '#000';
  x.fillRect(0, 0, S, S);
  draw(x);
  return x.getImageData(0, 0, S, S).data;
}

let glossTex: THREE.Texture | undefined;
function gloss(): THREE.Texture {
  if (glossTex) return glossTex;
  const grey = (v: number) => `rgb(${Math.round(v * 255)},${Math.round(v * 255)},${Math.round(v * 255)})`;

  const body = layer((x) => {
    const g = x.createLinearGradient(0, 0, 0, S);
    g.addColorStop(0, grey(1));
    g.addColorStop(0.3, grey(0.82));
    g.addColorStop(0.5, grey(0.6));
    g.addColorStop(0.56, grey(0.36)); // the horizon of the reflection
    g.addColorStop(0.82, grey(0.2));
    g.addColorStop(1, grey(0.34)); // light bouncing up from the floor
    x.fillStyle = g;
    x.fillRect(0, 0, S, S);
  });

  const shine = layer((x) => {
    x.shadowColor = '#fff';
    x.shadowBlur = 10;
    x.fillStyle = '#fff';
    // a soft box light, upper left
    x.save();
    x.translate(92, 66);
    x.rotate(-0.42);
    x.beginPath();
    x.roundRect(-34, -15, 68, 30, 9);
    x.fill();
    x.restore();
    // a thin strip light on the right
    x.shadowBlur = 8;
    x.fillStyle = 'rgba(255,255,255,0.5)';
    x.save();
    x.translate(186, 104);
    x.rotate(0.2);
    x.beginPath();
    x.roundRect(-5, -40, 10, 80, 5);
    x.fill();
    x.restore();
  });

  const rim = layer((x) => {
    x.fillStyle = '#fff';
    x.fillRect(0, 0, S, S); // beyond the ball's edge: full rim, so grazing surfaces never fall into black
    const g = x.createRadialGradient(S / 2, S / 2, S * 0.3, S / 2, S / 2, S * 0.5);
    g.addColorStop(0, '#000');
    g.addColorStop(0.55, grey(0.1));
    g.addColorStop(0.85, grey(0.5));
    g.addColorStop(1, '#fff');
    x.fillStyle = g;
    x.beginPath();
    x.arc(S / 2, S / 2, S / 2, 0, Math.PI * 2);
    x.fill();
    // less rim at the top, where the body is already bright
    const v = x.createLinearGradient(0, 0, 0, S);
    v.addColorStop(0, 'rgba(0,0,0,0.6)');
    v.addColorStop(0.5, 'rgba(0,0,0,0.12)');
    v.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = v;
    x.fillRect(0, 0, S, S);
  });

  const out = new Uint8Array(S * S * 4);
  for (let y = 0; y < S; y++) {
    for (let px = 0; px < S; px++) {
      const i = y * S + px; // in the drawings, row 0 is the top
      const o = (S - 1 - y) * S + px; // in the texture, row 0 is the bottom
      // drawn as it should look; stored as light (the renderer brightens on the way out)
      out[o * 4] = Math.round(Math.pow(body[i * 4] / 255, 2.2) * 255);
      out[o * 4 + 1] = Math.round(Math.pow(shine[i * 4] / 255, 2.2) * 255);
      out[o * 4 + 2] = Math.round(Math.pow(rim[i * 4] / 255, 2.2) * 255);
      out[o * 4 + 3] = 255;
    }
  }
  const t = new THREE.DataTexture(out, S, S, THREE.RGBAFormat);
  t.colorSpace = THREE.NoColorSpace;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearFilter;
  t.needsUpdate = true;
  t.userData.shared = true;
  glossTex = t;
  return t;
}

/** A polished, coloured surface with white highlights and a neon rim. Each call is its own material. */
export function glossMaterial(params: THREE.MeshMatcapMaterialParameters): THREE.MeshMatcapMaterial {
  const m = new THREE.MeshMatcapMaterial({ ...params, matcap: gloss() });
  m.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace(
      'vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;',
      `vec3 rimTint = mix( vec3( 0.22, 0.72, 1.0 ), diffuseColor.rgb, 0.5 );
	vec3 outgoingLight = diffuseColor.rgb * ( 0.1 + 1.05 * matcapColor.r ) + vec3( matcapColor.g ) * 0.8 + rimTint * matcapColor.b * 0.9;`
    );
  };
  m.customProgramCacheKey = () => 'gloss-2';
  return m;
}

const matCache = new Map<string, THREE.Material>();

/** A shared material. Glossy by default; `basic` is flat colour (panels, glows). Never disposed. */
export function mat(
  color: number,
  opts: { opacity?: number; basic?: boolean; side?: THREE.Side; map?: THREE.Texture; add?: boolean } = {}
): THREE.Material {
  const key = `${color}|${opts.opacity ?? 1}|${opts.basic ? 1 : 0}|${opts.side ?? 0}|${opts.map?.uuid ?? ''}|${opts.add ? 1 : 0}`;
  let m = matCache.get(key);
  if (!m) {
    const common = {
      color,
      transparent: (opts.opacity ?? 1) < 1 || !!opts.add,
      opacity: opts.opacity ?? 1,
      side: opts.side ?? THREE.FrontSide,
      depthWrite: (opts.opacity ?? 1) >= 1 && !opts.add,
      map: opts.map ?? null,
    };
    m = opts.basic
      ? new THREE.MeshBasicMaterial({ ...common, blending: opts.add ? THREE.AdditiveBlending : THREE.NormalBlending })
      : glossMaterial(common);
    m.userData.shared = true;
    matCache.set(key, m);
  }
  return m;
}

/** A box with a small bevel, standing on its base (y = 0 is the bottom). */
export function softBox(w: number, h: number, d: number, r?: number): THREE.BufferGeometry {
  const want = r !== undefined ? r * 0.5 : Math.min(w, d) * 0.09;
  const rad = Math.min(want, w / 2 - 0.001, h / 2 - 0.001, d / 2 - 0.001);
  const g = rad > 0.004 ? new RoundedBoxGeometry(w, h, d, 2, rad) : new THREE.BoxGeometry(w, h, d);
  g.translate(0, h / 2, 0);
  return g;
}

let glowTex: THREE.Texture | undefined;
/** A soft round glow (white in the middle, fading out). */
export function glowTexture(): THREE.Texture {
  if (glowTex) return glowTex;
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const x = c.getContext('2d')!;
  const g = x.createRadialGradient(64, 64, 2, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.25, 'rgba(255,255,255,0.55)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g;
  x.fillRect(0, 0, 128, 128);
  glowTex = new THREE.CanvasTexture(c);
  glowTex.colorSpace = THREE.SRGBColorSpace;
  glowTex.userData.shared = true;
  return glowTex;
}

/** A flat glow that can sit on the floor (a pool of light) or behind something (a halo). */
export function glow(size: number, color: number, opacity = 0.6, floor = false): THREE.Mesh {
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(size, size),
    new THREE.MeshBasicMaterial({ map: glowTexture(), color, transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending })
  );
  if (floor) m.rotation.x = -Math.PI / 2;
  return m;
}

/** A thin ring of light lying flat (around pedestals, decks, stands). */
export function neonRing(radius: number, color = NEON, tube = 0.012): THREE.Mesh {
  const m = new THREE.Mesh(new THREE.TorusGeometry(radius, tube, 8, 64), new THREE.MeshBasicMaterial({ color }));
  m.rotation.x = Math.PI / 2;
  return m;
}

/** A sheet of dark glass that floats: soft corners, a hair-thin bright edge, a faint reflection. Nothing else. */
export function panel(w: number, h: number, opts: { fill?: string; edge?: string; radius?: number } = {}): THREE.Mesh {
  const px = 512;
  const c = document.createElement('canvas');
  c.width = Math.round(px * Math.min(4, Math.max(1, w / h)));
  c.height = Math.round(px * Math.min(4, Math.max(1, h / w)));
  const W = c.width;
  const H = c.height;
  const x = c.getContext('2d')!;
  const unit = H / h; // canvas pixels per metre
  const r = Math.min((opts.radius ?? 0.07) * unit, H * 0.2, W * 0.2);
  const m0 = 3;
  const shape = () => {
    x.beginPath();
    x.roundRect(m0, m0, W - m0 * 2, H - m0 * 2, r);
  };
  // the glass itself: dark and see-through, a little lighter at the top
  shape();
  const g = x.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, opts.fill ?? 'rgba(13,22,52,0.72)');
  g.addColorStop(1, 'rgba(5,9,24,0.78)');
  x.fillStyle = g;
  x.fill();
  // one soft reflection running across it
  x.save();
  shape();
  x.clip();
  const sh = x.createLinearGradient(0, 0, W * 0.55, H);
  sh.addColorStop(0, 'rgba(255,255,255,0.1)');
  sh.addColorStop(0.35, 'rgba(255,255,255,0.03)');
  sh.addColorStop(0.36, 'rgba(255,255,255,0)');
  sh.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = sh;
  x.fillRect(0, 0, W, H);
  x.restore();
  // the edge: one thin line, brighter along the top
  shape();
  const e = x.createLinearGradient(0, 0, 0, H);
  e.addColorStop(0, opts.edge ?? 'rgba(210,238,255,0.95)');
  e.addColorStop(1, 'rgba(120,190,255,0.55)');
  x.lineWidth = 2;
  x.strokeStyle = e;
  x.stroke();
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  // Drawn before the text that sits on it, and it hides what is behind it: without this, lines far from the
  // middle of a big panel were painted first and then covered by the panel itself.
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(w, h),
    new THREE.MeshBasicMaterial({ map: t, transparent: true, side: THREE.DoubleSide, depthWrite: true, alphaTest: 0.3 })
  );
  m.renderOrder = -1;
  return m;
}

export interface ButtonOpts extends LabelOpts {
  /** Colour of the plate behind the text. */
  plate?: number;
  tip?: string;
  minW?: number;
}

export interface Button extends THREE.Group {
  setActive(on: boolean): void;
}

/** A glossy key with a lit frame: point at it and pull the trigger. */
export function button(engine: Engine, text: string, onClick: () => void, o: ButtonOpts = {}): Button {
  const g = new THREE.Group() as Button;
  const label = makeLabel(text, { h: 0.12, px: 64, weight: '700', ...o });
  const w = Math.max(label.userData.w + 0.14, o.minW ?? 0);
  const h = label.userData.hgt + 0.08;
  const base = o.plate ?? 0x2447c4;
  const plateMat = glossMaterial({ color: base });
  const plate = new THREE.Mesh(new RoundedBoxGeometry(w, h, 0.06, 2, Math.min(0.014, h / 2 - 0.002)), plateMat);
  plate.position.z = -0.035;
  const frameMat = new THREE.MeshBasicMaterial({ color: NEON });
  const frame = new THREE.Mesh(new THREE.BoxGeometry(w + 0.026, h + 0.026, 0.03), frameMat);
  frame.position.z = -0.052;
  label.position.z = 0.002;
  g.add(frame, plate, label);
  g.userData.w = w;
  g.userData.h = h;
  let active = false;
  const paint = (hover: boolean) => {
    plateMat.color.setHex(active ? 0x0fa890 : base);
    if (hover) plateMat.color.offsetHSL(0, 0, 0.12);
    frameMat.color.setHex(hover ? 0xffffff : active ? 0x7dffd8 : NEON);
    g.scale.setScalar(hover ? 1.06 : 1);
  };
  g.setActive = (on: boolean) => {
    active = on;
    paint(false);
  };
  engine.register(g, {
    select: () => {
      tween(0.18, (k) => (g.position.z = Math.sin(k * Math.PI) * -0.03 + (g.userData.z0 ?? (g.userData.z0 = g.position.z))));
      onClick();
    },
    hover: paint,
    tip: o.tip,
  });
  return g;
}

/** Lays items out in a row, centred on x = 0. */
export function row(items: THREE.Object3D[], gap = 0.08): THREE.Group {
  const g = new THREE.Group();
  const total = items.reduce((s, b) => s + (b.userData.w ?? 0.3), 0) + gap * (items.length - 1);
  let x = -total / 2;
  for (const b of items) {
    const w = b.userData.w ?? 0.3;
    b.position.x = x + w / 2;
    x += w + gap;
    g.add(b);
  }
  g.userData.w = total;
  return g;
}

/** A machined stand: a wide foot, a slim column, a top plate, two rings of light and a pool of light under it. */
export function pedestal(radius: number, height: number, color = STEEL): THREE.Group {
  const g = new THREE.Group();
  const foot = Math.min(0.09, height * 0.25);
  const cap = Math.min(0.07, height * 0.2);
  const pts = [
    new THREE.Vector2(0, 0),
    new THREE.Vector2(radius * 1.22, 0),
    new THREE.Vector2(radius * 1.22, foot * 0.55),
    new THREE.Vector2(radius * 1.05, foot),
    new THREE.Vector2(radius * 0.46, foot + 0.03),
    new THREE.Vector2(radius * 0.4, height - cap - 0.05),
    new THREE.Vector2(radius * 0.98, height - cap),
    new THREE.Vector2(radius * 1.04, height - cap * 0.5),
    new THREE.Vector2(radius * 1.04, height),
    new THREE.Vector2(0, height),
  ];
  g.add(new THREE.Mesh(new THREE.LatheGeometry(pts, 40), mat(color)));
  const low = neonRing(radius * 1.24, NEON, 0.012);
  low.position.y = foot * 0.55;
  const high = neonRing(radius * 1.06, NEON, 0.01);
  high.position.y = height - cap * 0.5;
  g.add(low, high);
  const pool = glow(radius * 5, NEON, 0.4, true);
  pool.position.y = 0.02;
  g.add(pool);
  return g;
}

/** A station's sign: a big name and one or two lines that say what to do. Always faces the viewer. */
export function sign(engine: Engine, title: string, how: string, y: number, color = '#ffd58a'): THREE.Group {
  const holder = new THREE.Group();
  const t = makeLabel(title, { h: 0.19, weight: '800', color, px: 80, display: true });
  const h = makeLabel(how, { h: 0.105, weight: '600', color: '#e6f4ff', px: 60 });
  const w = Math.max(t.userData.w, h.userData.w) + 0.3;
  const hh = t.userData.hgt + h.userData.hgt + 0.2;
  const back = panel(w, hh);
  back.position.z = -0.01;
  t.position.y = hh / 2 - 0.1 - t.userData.hgt / 2;
  h.position.y = -hh / 2 + 0.08 + h.userData.hgt / 2;
  holder.add(back, t, h);
  holder.position.y = y;
  holder.userData.hgt = hh;
  engine.billboards.add(holder);
  return holder;
}
