// A hand controller drawn in the room, shaped after the ones of the newer headsets (no ring): a round, dark,
// matt face with a thumb stick, two buttons and a small menu button; a white matt plastic body that curves down
// into the palm; a trigger in front and a grip on the inner side.
// In the headset one is drawn on each real controller. On a PC one follows the mouse instead of the arrow, and
// its trigger and grip move when the mouse buttons are pressed.
//
// The model's origin is where the pointing ray starts; it points down its own -Z.

import * as THREE from 'three';

import { makeLabel } from './text';

export interface Controller {
  group: THREE.Group;
  /** Shows the trigger (left mouse button) or the grip (right mouse button) pressed. */
  press(what: 'trigger' | 'grip', on: boolean): void;
  /** Tilts the thumb stick: x and y from -1 to 1. */
  stick(x: number, y: number): void;
  update(dt: number): void;
}

let plasticTex: THREE.Texture | undefined;
/** Shading of a matt plastic ball in soft light: no sharp reflections, no rim of light. */
function plastic(): THREE.Texture {
  if (plasticTex) return plasticTex;
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const x = c.getContext('2d')!;
  x.fillStyle = '#6c6c74';
  x.fillRect(0, 0, 256, 256);
  let g = x.createRadialGradient(104, 88, 10, 128, 128, 134);
  g.addColorStop(0, '#ffffff');
  g.addColorStop(0.4, '#ededf0');
  g.addColorStop(0.75, '#c2c2c9');
  g.addColorStop(1, '#84848d');
  x.fillStyle = g;
  x.beginPath();
  x.arc(128, 128, 128, 0, Math.PI * 2);
  x.fill();
  // a wide, weak sheen instead of a highlight
  g = x.createRadialGradient(92, 74, 0, 92, 74, 60);
  g.addColorStop(0, 'rgba(255,255,255,0.35)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g;
  x.fillRect(20, 10, 150, 140);
  plasticTex = new THREE.CanvasTexture(c);
  plasticTex.colorSpace = THREE.SRGBColorSpace;
  plasticTex.userData.shared = true;
  return plasticTex;
}

const shared = new Map<number, THREE.MeshMatcapMaterial>();
function matt(color: number, own = false): THREE.MeshMatcapMaterial {
  if (own) return new THREE.MeshMatcapMaterial({ color, matcap: plastic() });
  let m = shared.get(color);
  if (!m) {
    m = new THREE.MeshMatcapMaterial({ color, matcap: plastic() });
    m.userData.shared = true;
    shared.set(color, m);
  }
  return m;
}

const WHITE = 0xf1f2f5;
const FACE = 0x46474d;
const KEY = 0x2f3035;

export function makeController(side: 'left' | 'right'): Controller {
  const group = new THREE.Group();
  const s = side === 'left' ? -1 : 1; // +1: things that are on the right of a right-hand controller
  const white = matt(WHITE);
  const face = matt(FACE);
  const key = matt(KEY);

  // ---- the head: a dark, slightly domed face leaning back towards the person, on a white bowl
  const head = new THREE.Group();
  head.position.set(0, -0.016, 0.04);
  head.rotation.x = 0.66;
  const top = new THREE.Mesh(new THREE.SphereGeometry(0.0375, 40, 20), face);
  top.scale.y = 0.2;
  top.position.y = 0.0045;
  const bowl = new THREE.Mesh(new THREE.SphereGeometry(0.0368, 40, 20, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), white);
  bowl.scale.y = 0.62;
  bowl.position.y = 0.0045;
  head.add(top, bowl);

  // the thumb stick (outer, far side) on its small base
  const stickBase = new THREE.Group();
  stickBase.position.set(0.012 * s, 0.0105, -0.012);
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.0085, 0.0095, 0.003, 22), key);
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.0038, 0.0045, 0.009, 12), key);
  stem.position.y = 0.0055;
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.0088, 0.0094, 0.0045, 24), key);
  cap.position.y = 0.0115;
  const dimple = new THREE.Mesh(new THREE.CylinderGeometry(0.0058, 0.0058, 0.0008, 20), matt(0x3b3c42));
  dimple.position.y = 0.0139;
  stickBase.add(collar, stem, cap, dimple);
  head.add(stickBase);

  // two round buttons (inner side) and the small menu button
  const letters = side === 'left' ? ['Y', 'X'] : ['B', 'A'];
  const spots: [number, number][] = [
    [-0.0135 * s, -0.008],
    [-0.006 * s, 0.0085],
  ];
  spots.forEach(([bx, bz], i) => {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.0064, 0.0068, 0.0036, 20), key);
    b.position.set(bx, 0.0112, bz);
    const l = makeLabel(letters[i], { h: 0.0062, px: 48, weight: '700', color: '#c9ccd4' });
    l.rotation.x = -Math.PI / 2;
    l.position.set(bx, 0.0133, bz);
    head.add(b, l);
  });
  const menu = new THREE.Mesh(new THREE.CylinderGeometry(0.0042, 0.0045, 0.0026, 16), key);
  menu.position.set(0.0125 * s, 0.0106, 0.0125);
  head.add(menu);

  // ---- the body: curves down and back into the palm, a little thicker in the middle
  // (it starts under the middle of the face, so from above nothing white covers the face)
  const path = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, -0.034, 0.03),
    new THREE.Vector3(-0.002 * s, -0.052, 0.054),
    new THREE.Vector3(-0.004 * s, -0.071, 0.071),
    new THREE.Vector3(-0.006 * s, -0.086, 0.08),
  ]);
  const body = new THREE.Mesh(new THREE.TubeGeometry(path, 24, 0.0195, 16), white);
  const end = new THREE.Mesh(new THREE.SphereGeometry(0.0195, 16, 12), white);
  end.position.copy(path.getPoint(1));
  const neck = new THREE.Mesh(new THREE.SphereGeometry(0.022, 20, 14), white);
  neck.scale.set(1, 0.9, 1.05);
  neck.position.set(0, -0.037, 0.034);
  const palm = new THREE.Mesh(new THREE.SphereGeometry(0.021, 20, 14), white);
  palm.scale.set(1.04, 1.25, 1.08);
  palm.position.copy(path.getPoint(0.55));
  palm.rotation.x = -1.0;

  // ---- trigger (index finger, in front under the head) and grip (middle finger, inner side of the body)
  const triggerMat = matt(0xe4e6eb, true);
  const trigger = new THREE.Mesh(new THREE.SphereGeometry(0.0115, 16, 12), triggerMat);
  trigger.scale.set(0.8, 1.25, 1.0);
  trigger.position.set(0, -0.036, 0.022);
  trigger.rotation.x = -0.5;
  const gripMat = matt(0xe4e6eb, true);
  const grip = new THREE.Mesh(new THREE.CapsuleGeometry(0.0058, 0.015, 4, 12), gripMat);
  grip.position.set(-0.0185 * s, -0.062, 0.062);
  grip.rotation.x = -0.95;

  void palm; // the bulge made the short grip look lumpy; the plain tube reads better
  group.add(head, neck, body, end, trigger, grip);

  let trig = 0;
  let trigWant = 0;
  let grp = 0;
  let grpWant = 0;
  const stickWant = new THREE.Vector2();
  const stickNow = new THREE.Vector2();
  const idle = new THREE.Color(0xe4e6eb);
  const lit = new THREE.Color(0x7fd4ff);
  return {
    group,
    press(what, on) {
      if (what === 'trigger') trigWant = on ? 1 : 0;
      else grpWant = on ? 1 : 0;
    },
    stick(x, y) {
      stickWant.set(x, y);
    },
    update(dt) {
      const k = 1 - Math.exp(-dt * 22);
      trig += (trigWant - trig) * k;
      grp += (grpWant - grp) * k;
      // the trigger is squeezed back into the body, the grip is pushed in
      trigger.position.z = 0.022 + trig * 0.009;
      trigger.position.y = -0.036 + trig * 0.004;
      triggerMat.color.copy(idle).lerp(lit, trig * 0.75);
      grip.position.x = (-0.0185 + grp * 0.0045) * s;
      gripMat.color.copy(idle).lerp(lit, grp * 0.75);
      stickNow.lerp(stickWant, 1 - Math.exp(-dt * 14));
      stickBase.rotation.z = -stickNow.x * 0.42;
      stickBase.rotation.x = -stickNow.y * 0.42;
    },
  };
}
