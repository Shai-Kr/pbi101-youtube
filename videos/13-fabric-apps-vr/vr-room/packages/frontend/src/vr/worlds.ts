// The place: a station deck in SPACE.
// The world is also a reading of the data: the light in its sky follows "this year against last year".

import * as THREE from 'three';

import { fmtPct } from './data';
import { makeLabel, setLabel } from './text';
import { glow, glowTexture, mat, neonRing, NEON, STEEL } from './ui';

export type WorldName = 'space';

export interface World {
  name: WorldName;
  group: THREE.Group;
  /** How far the viewer may walk from the middle. */
  radius: number;
  /** Growth against last year for whatever is filtered now; NaN when it cannot be computed. */
  setAmbient(pct: number, what: string): void;
  update(dt: number, t: number): void;
}

function canvasTex(w: number, h: number, draw: (x: CanvasRenderingContext2D) => void, repeat?: [number, number]): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  draw(c.getContext('2d')!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (repeat) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(repeat[0], repeat[1]);
  }
  return t;
}

function gradientTexture(stops: [number, string][]): THREE.CanvasTexture {
  return canvasTex(16, 512, (x) => {
    const g = x.createLinearGradient(0, 0, 0, 512);
    for (const [p, col] of stops) g.addColorStop(p, col);
    x.fillStyle = g;
    x.fillRect(0, 0, 16, 512);
  });
}

const GOOD = new THREE.Color(0x34d399);
const BAD = new THREE.Color(0xf87171);
const FLAT = new THREE.Color(0x93c5fd);

function moodColor(pct: number, out = new THREE.Color()): THREE.Color {
  if (!isFinite(pct)) return out.copy(FLAT);
  const k = THREE.MathUtils.clamp(Math.abs(pct) / 0.08, 0, 1);
  return out.copy(FLAT).lerp(pct >= 0 ? GOOD : BAD, 0.35 + 0.65 * k);
}

/** Round, soft stars in three sizes, in gently different colours. */
function stars(group: THREE.Group, count: number, size: number, rMin: number, rMax: number, opacity: number): THREE.Points {
  const pos: number[] = [];
  const col: number[] = [];
  const c = new THREE.Color();
  for (let i = 0; i < count; i++) {
    const v = new THREE.Vector3().randomDirection().multiplyScalar(rMin + Math.random() * (rMax - rMin));
    pos.push(v.x, v.y, v.z);
    const pick = Math.random();
    c.setHSL(pick < 0.6 ? 0.6 : pick < 0.85 ? 0.12 : 0.95, 0.55, 0.78 + Math.random() * 0.22);
    col.push(c.r, c.g, c.b);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const p = new THREE.Points(
    g,
    new THREE.PointsMaterial({
      size,
      map: glowTexture(),
      vertexColors: true,
      transparent: true,
      opacity,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      fog: false,
      sizeAttenuation: true,
    })
  );
  group.add(p);
  return p;
}

// ---------------------------------------------------------------------------------------------- SPACE

export function buildSpace(): World {
  const group = new THREE.Group();

  // deep sky
  const sky = new THREE.Mesh(
    new THREE.SphereGeometry(480, 32, 20),
    new THREE.MeshBasicMaterial({
      map: gradientTexture([
        [0, '#070a1f'],
        [0.3, '#0e1640'],
        [0.5, '#241a52'],
        [0.64, '#0d1335'],
        [1, '#04050d'],
      ]),
      side: THREE.BackSide,
      fog: false,
    })
  );
  group.add(sky);

  // soft clouds of colour far away
  const nebula: [number, number, number, number, number][] = [
    [-260, 150, -300, 420, 0x6d4bd8],
    [240, 110, -330, 380, 0x2f7fd6],
    [60, 230, -260, 340, 0xd65fa8],
    [-320, 60, 120, 400, 0x2aa6a0],
    [300, 180, 200, 420, 0x5b4fd0],
    [0, 120, 380, 460, 0x3b6fd8],
    [-120, 320, 60, 380, 0x8a4fd0],
  ];
  for (const [x, y, z, s, color] of nebula) {
    const n = glow(s, color, 0.34);
    n.position.set(x, y, z);
    n.lookAt(0, 0, 0);
    (n.material as THREE.MeshBasicMaterial).fog = false;
    group.add(n);
  }

  const layers = [stars(group, 1500, 1.5, 150, 420, 0.9), stars(group, 380, 3.2, 180, 420, 1), stars(group, 60, 7, 200, 420, 1)];

  // a far planet with a thin ring and a small moon, for depth
  const far = new THREE.Mesh(new THREE.SphereGeometry(26, 32, 20), mat(0x7b6fd0));
  far.position.set(-190, 70, -150);
  const farGlow = glow(110, 0x8f7fff, 0.4);
  farGlow.position.copy(far.position);
  farGlow.lookAt(0, 0, 0);
  const moon = new THREE.Mesh(new THREE.SphereGeometry(7, 20, 14), mat(0xc9d2e8));
  moon.position.set(170, 95, 150);
  group.add(farGlow, far, moon);

  // ---- the deck: a station platform of glowing hexagons
  const hex = canvasTex(
    512,
    512,
    (x) => {
      x.fillStyle = '#04081a';
      x.fillRect(0, 0, 512, 512);
      const R = 512 / 6;
      const w = R * Math.sqrt(3);
      x.lineWidth = 3;
      x.shadowColor = 'rgba(80,210,255,0.9)';
      x.shadowBlur = 9;
      for (let row = -1; row < 6; row++) {
        for (let col = -1; col < 5; col++) {
          const cx = col * w + (row % 2 ? w / 2 : 0);
          const cy = row * R * 1.5;
          x.beginPath();
          for (let i = 0; i < 6; i++) {
            const a = (Math.PI / 3) * i + Math.PI / 6;
            const px = cx + Math.cos(a) * (R - 5);
            const py = cy + Math.sin(a) * (R - 5);
            if (i) x.lineTo(px, py);
            else x.moveTo(px, py);
          }
          x.closePath();
          const g = x.createRadialGradient(cx, cy, 2, cx, cy, R);
          g.addColorStop(0, '#0a1330');
          g.addColorStop(0.7, '#060b20');
          g.addColorStop(1, '#030612');
          x.fillStyle = g;
          x.fill();
          x.strokeStyle = 'rgba(96,222,255,0.95)';
          x.stroke();
        }
      }
    },
    [9, 9 * (Math.sqrt(3) / 2) * (2 / 1.5) * 0.866]
  );
  const deck = new THREE.Mesh(new THREE.CircleGeometry(15, 72), new THREE.MeshBasicMaterial({ map: hex }));
  deck.rotation.x = -Math.PI / 2;
  group.add(deck);
  // light from above, mirrored in the polished deck
  const sheen = glow(22, 0x3b7bff, 0.1, true);
  sheen.position.y = 0.008;
  group.add(sheen);
  // a dark metal rim with a line of light, a glass rail and lamps around the edge
  const rim = new THREE.Mesh(new THREE.TorusGeometry(15.1, 0.22, 12, 96), mat(STEEL));
  rim.rotation.x = Math.PI / 2;
  rim.position.y = 0.05;
  const rimLight = neonRing(15.1, NEON, 0.03);
  rimLight.position.y = 0.28;
  group.add(rimLight);
  // two huge rings of the station, far out, turning slowly
  const orbit: THREE.Mesh[] = [];
  for (const [r, tilt, color, o] of [
    [80, 0.22, 0x5fd8ff, 0.34],
    [120, -0.16, 0x8f6bff, 0.3],
  ]) {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(r, 0.35, 6, 160),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: o, fog: false, blending: THREE.AdditiveBlending, depthWrite: false })
    );
    ring.rotation.set(Math.PI / 2 + tilt, 0, tilt * 0.6);
    ring.position.y = 34;
    orbit.push(ring);
    group.add(ring);
  }
  const railTex = gradientTexture([
    [0, 'rgba(125,211,252,0.0)'],
    [0.7, 'rgba(125,211,252,0.10)'],
    [1, 'rgba(125,211,252,0.55)'],
  ]);
  const rail = new THREE.Mesh(
    new THREE.CylinderGeometry(15.1, 15.1, 1.1, 72, 1, true),
    new THREE.MeshBasicMaterial({ map: railTex, transparent: true, side: THREE.DoubleSide, depthWrite: false })
  );
  rail.position.y = 0.6;
  group.add(rim, rail);
  const lampMat = new THREE.MeshBasicMaterial({ color: 0x7dd3fc });
  const lamps: THREE.Mesh[] = [];
  for (let i = 0; i < 24; i++) {
    const a = (i / 24) * Math.PI * 2;
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.06, 1.15, 6), mat(STEEL));
    post.position.set(Math.sin(a) * 15.1, 0.6, Math.cos(a) * 15.1);
    const lamp = new THREE.Mesh(new THREE.OctahedronGeometry(0.12, 0), lampMat);
    lamp.position.set(post.position.x, 1.22, post.position.z);
    const halo = glow(0.9, 0x7dd3fc, 0.55);
    halo.position.copy(lamp.position);
    halo.lookAt(0, 1.22, 0);
    group.add(post, lamp, halo);
    lamps.push(lamp);
  }
  // rings of light that travel outwards across the deck
  const pulseMat = new THREE.MeshBasicMaterial({ color: 0x7dd3fc, transparent: true, opacity: 0.5, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending });
  const pulses: THREE.Mesh[] = [];
  for (let i = 0; i < 3; i++) {
    const p = new THREE.Mesh(new THREE.RingGeometry(0.96, 1, 96), pulseMat.clone());
    p.rotation.x = -Math.PI / 2;
    p.position.y = 0.012;
    pulses.push(p);
    group.add(p);
  }
  const under = glow(70, 0x3050d0, 0.3, true);
  under.position.y = -3;
  group.add(under);

  // the aurora: slow ribbons of light whose colour says how this year compares with last year
  const ribbons: THREE.Mesh[] = [];
  const alpha = gradientTexture([
    [0, '#000000'],
    [0.45, '#ffffff'],
    [1, '#000000'],
  ]);
  for (let i = 0; i < 3; i++) {
    const m = new THREE.Mesh(
      new THREE.CylinderGeometry(110 + i * 14, 110 + i * 14, 18 + i * 5, 48, 1, true, -1.0 + i * 0.3, 1.9),
      new THREE.MeshBasicMaterial({ color: 0x34d399, alphaMap: alpha, transparent: true, opacity: 0.3, side: THREE.BackSide, depthWrite: false, blending: THREE.AdditiveBlending, fog: false })
    );
    m.position.y = 78 + i * 11;
    m.rotation.y = Math.PI;
    ribbons.push(m);
    group.add(m);
  }

  const sign = makeLabel('Aurora light', { h: 0.26, color: '#bfe9ff', px: 72, weight: '700' });
  sign.position.set(0, 0.02, -4.4);
  sign.rotation.x = -Math.PI / 2;
  group.add(sign);

  const target = new THREE.Color(0x34d399);
  let strength = 0.3;
  return {
    name: 'space',
    group,
    radius: 14.2,
    setAmbient(pct, what) {
      moodColor(pct, target);
      strength = isFinite(pct) ? 0.16 + Math.min(Math.abs(pct) * 1.5, 0.3) : 0.1;
      setLabel(sign, isFinite(pct) ? `The light in the sky = this year against last year\n${what}: ${fmtPct(pct, true)}` : `The light in the sky = this year against last year\n${what}: nothing to compare`);
    },
    update(dt, t) {
      ribbons.forEach((r, i) => {
        const m = r.material as THREE.MeshBasicMaterial;
        m.color.lerp(target, Math.min(1, dt * 2));
        m.opacity = strength * (0.75 + 0.25 * Math.sin(t * 0.5 + i * 1.7));
        r.rotation.y = Math.PI + Math.sin(t * 0.07 + i) * 0.25;
      });
      lampMat.color.lerp(target, Math.min(1, dt * 2));
      layers.forEach((l, i) => ((l.material as THREE.PointsMaterial).opacity = 0.8 + 0.2 * Math.sin(t * (0.7 + i * 0.5) + i)));
      pulses.forEach((p, i) => {
        const k = (t * 0.12 + i / 3) % 1;
        p.scale.setScalar(1 + k * 14);
        (p.material as THREE.MeshBasicMaterial).opacity = 0.45 * (1 - k);
        (p.material as THREE.MeshBasicMaterial).color.copy(target);
      });
      far.rotation.y += dt * 0.02;
      orbit.forEach((o, i) => (o.rotation.z += dt * (i ? -0.006 : 0.009)));
      lamps.forEach((l, i) => {
        l.scale.setScalar(1 + 0.25 * Math.sin(t * 2 + i * 0.6));
        l.rotation.y = t * 0.8 + i;
      });
    },
  };
}
