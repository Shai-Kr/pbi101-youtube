// Text in the room: every label is a small canvas drawn once and shown on a flat plane.

import * as THREE from 'three';

import '@fontsource/exo-2/latin-500.css';
import '@fontsource/exo-2/latin-600.css';
import '@fontsource/exo-2/latin-700.css';
import '@fontsource/exo-2/latin-800.css';
import '@fontsource/orbitron/latin-700.css';
import '@fontsource/orbitron/latin-800.css';

export interface LabelOpts {
  /** Height of the plane in metres. */
  h?: number;
  color?: string;
  weight?: string;
  /** Background colour (with rounded corners) behind the text. */
  bg?: string;
  /** Font size on the canvas: bigger is sharper and heavier. */
  px?: number;
  align?: 'center' | 'left' | 'right';
  /** Draw on top of everything (tooltips). */
  onTop?: boolean;
  /** A thin bright frame around the background. */
  edge?: string;
  /** The wide display face (station names, big titles). */
  display?: boolean;
}

const FONT = '"Exo 2", "Segoe UI", system-ui, -apple-system, Roboto, sans-serif';
const DISPLAY = '"Orbitron", "Exo 2", "Segoe UI", system-ui, sans-serif';

/** Labels are drawn on a canvas once, so the faces must be loaded before the room is built. */
export function fontsReady(): Promise<unknown> {
  if (typeof document === 'undefined' || !document.fonts) return Promise.resolve();
  const wanted = ['500', '600', '700', '800'].map((w) => `${w} 32px "Exo 2"`).concat(['700 32px "Orbitron"', '800 32px "Orbitron"']);
  const all = Promise.all(wanted.map((f) => document.fonts.load(f).catch(() => undefined)));
  // never hold the room back for a font: three seconds at most, then the fallback face is used
  return Promise.race([all, new Promise((r) => setTimeout(r, 3000))]);
}

export function makeLabel(text: string, o: LabelOpts = {}): THREE.Mesh {
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false, side: THREE.DoubleSide })
  );
  mesh.userData.labelOpts = o;
  setLabel(mesh, text);
  if (o.onTop) {
    (mesh.material as THREE.MeshBasicMaterial).depthTest = false;
    mesh.renderOrder = 999;
  }
  return mesh;
}

/** Changes the text of a label made with makeLabel (redraws its canvas). */
export function setLabel(mesh: THREE.Mesh, text: string): void {
  if (mesh.userData.labelText === text) return;
  mesh.userData.labelText = text;
  const o: LabelOpts = mesh.userData.labelOpts ?? {};
  const h = o.h ?? 0.12;
  const px = o.px ?? 56;
  const lines = text.split('\n');
  const canvas: HTMLCanvasElement = mesh.userData.canvas ?? document.createElement('canvas');
  mesh.userData.canvas = canvas;
  const ctx = canvas.getContext('2d')!;
  const font = `${o.weight ?? '600'} ${px}px ${o.display ? DISPLAY : FONT}`;
  const spacing = o.display ? '0.06em' : '0.015em';
  ctx.font = font;
  (ctx as unknown as { letterSpacing: string }).letterSpacing = spacing;
  const pad = px * 0.45;
  const lineH = px * 1.28;
  const w = Math.max(...lines.map((l) => ctx.measureText(l).width));
  canvas.width = Math.max(8, Math.ceil(w + pad * 2));
  canvas.height = Math.ceil(lineH * lines.length + pad * 0.6);
  ctx.font = font;
  (ctx as unknown as { letterSpacing: string }).letterSpacing = spacing;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (o.bg) {
    // a small plate with soft corners, like the glass panels
    const e = o.edge ? 2 : 0;
    ctx.beginPath();
    ctx.roundRect(e, e, canvas.width - e * 2, canvas.height - e * 2, px * 0.22);
    ctx.fillStyle = o.bg;
    ctx.fill();
    if (o.edge) {
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = o.edge;
      ctx.stroke();
    }
  }
  ctx.fillStyle = o.color ?? '#eef3ff';
  ctx.textBaseline = 'middle';
  const align = o.align ?? 'center';
  ctx.textAlign = align;
  const x = align === 'center' ? canvas.width / 2 : align === 'left' ? pad : canvas.width - pad;
  lines.forEach((l, i) => ctx.fillText(l, x, pad * 0.3 + lineH * (i + 0.5)));

  const mat = mesh.material as THREE.MeshBasicMaterial;
  if (mat.map) mat.map.dispose();
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  mat.map = tex;
  mat.needsUpdate = true;

  const height = h * lines.length;
  const width = (height * canvas.width) / canvas.height;
  mesh.scale.set(width, height, 1);
  mesh.userData.w = width;
  mesh.userData.hgt = height;
}

/** Puts the left (or right) edge of a label at x, so rows of text line up. */
export function anchorLabel(mesh: THREE.Mesh, x: number, side: 'left' | 'right' = 'left'): void {
  mesh.position.x = side === 'left' ? x + mesh.userData.w / 2 : x - mesh.userData.w / 2;
}
