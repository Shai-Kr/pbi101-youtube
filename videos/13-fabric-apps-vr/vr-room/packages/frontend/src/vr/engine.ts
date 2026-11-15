// The engine: renderer, the viewer's "rig", the two hand controllers, pointing, grabbing from a distance,
// cutting, and slow, smooth movement (no jumps: gliding and turning ease in and out).
//
// Headset: left stick = glide · right stick = turn slowly · trigger = pick / press / cut · grip = grab
//          (a ball flies into the hand; point at the basket or the scales and let go, or throw it) ·
//          A / X = go inside what you point at (otherwise the menu) · B / Y = back
// PC twin: click = trigger · hold right button = grab · drag = look · W A S D = glide · Q / E = turn ·
//          F = go inside · X = cut · B = back · M = menu · wheel = push / pull a held object

import * as THREE from 'three';
import { VRButton } from 'three/addons/webxr/VRButton.js';

import { makeController, type Controller } from './controller';
import { makeLabel, setLabel } from './text';

export interface Interact {
  /** Short text shown next to the pointer while hovering. */
  tip?: string | (() => string);
  hover?(on: boolean): void;
  /** Trigger. */
  select?(hand: Hand): void;
  /** A / X while pointing: go inside. */
  enter?(hand: Hand): void;
  /** A fast swing of the controller through the object (the trigger cuts too when there is no `select`). */
  slice?(hand: Hand): void;
  /** Grip: pick up. `pull` brings it into the hand, so it can then be sent somewhere by pointing. */
  grab?: { onGrab?(hand: Hand): void; onRelease?(hand: Hand): void; scale?: boolean; pull?: boolean };
}

export interface Hand {
  id: number;
  side: 'left' | 'right' | 'mouse';
  /** Pointer pose: looks down its own -Z. */
  ray: THREE.Object3D;
  line: THREE.Line;
  hover: THREE.Object3D | null;
  hoverPoint: THREE.Vector3;
  hoverDist: number;
  grabbed: THREE.Object3D | null;
  grabParent: THREE.Object3D | null;
  tip: THREE.Vector3;
  vel: THREE.Vector3;
  speed: number;
  squeezing: boolean;
  buttons: boolean[];
  sliceCooldown: number;
  aimed: DropZone | null;
}

export interface DropZone {
  /** World position of the zone's centre. */
  center(): THREE.Vector3;
  radius: number;
  accepts(obj: THREE.Object3D): boolean;
  drop(obj: THREE.Object3D): void;
  /** Lights up while a held object is aimed at it. */
  highlight?(on: boolean): void;
}

const tmpV = new THREE.Vector3();
const tmpV2 = new THREE.Vector3();
const tmpV3 = new THREE.Vector3();
const tmpQ = new THREE.Quaternion();
const tmpBox = new THREE.Box3();
const UP = new THREE.Vector3(0, 1, 0);

export function itOf(obj: THREE.Object3D | null): { root: THREE.Object3D; it: Interact } | null {
  for (let o = obj; o; o = o.parent) {
    if (o.userData.it) return { root: o, it: o.userData.it as Interact };
  }
  return null;
}

function shown(obj: THREE.Object3D): boolean {
  for (let o: THREE.Object3D | null = obj; o; o = o.parent) if (!o.visible) return false;
  return true;
}

export class Engine {
  readonly renderer: THREE.WebGLRenderer;
  readonly scene = new THREE.Scene();
  readonly camera: THREE.PerspectiveCamera;
  /** The viewer's body: gliding and turning move this, the headset moves the camera inside it. */
  readonly rig = new THREE.Group();
  readonly hands: Hand[] = [];
  readonly targets = new Set<THREE.Object3D>();
  readonly sliceables = new Set<THREE.Object3D>();
  readonly billboards = new Set<THREE.Object3D>();
  readonly zones: DropZone[] = [];
  readonly frame: ((dt: number, t: number) => void)[] = [];
  /** How far from the middle the viewer may go. */
  walkRadius = 14;
  /** Metres per second at full stick: a slow walk. */
  glideSpeed = 1.3;
  /** Radians per second at full stick: about 35 degrees a second. */
  turnSpeed = 0.6;
  onMenu: () => void = () => {};
  onBack: () => void = () => {};
  onAnyInput: () => void = () => {};

  private raycaster = new THREE.Raycaster();
  private clock = new THREE.Clock();
  private tooltip: THREE.Mesh;
  private fadeMesh: THREE.Mesh;
  private fadeJob: { t: number; mid: () => void; done: boolean } | null = null;
  private mouse: Hand;
  private yaw = 0;
  private pitch = 0;
  private keys = new Set<string>();
  private twoHand: { obj: THREE.Object3D; d0: number; s0: number } | null = null;
  private disposers: (() => void)[] = [];
  private el: HTMLElement;
  private move = new THREE.Vector2(); // smoothed glide (x = sideways, y = forward), metres per second
  private turn = 0; // smoothed turn, radians per second
  private flying: { obj: THREE.Object3D; from: THREE.Vector3; zone: DropZone; t: number; dur: number; lift: number }[] = [];
  private xrModels: Controller[] = [];
  private pcRight!: Controller;
  private pcLeft!: Controller;
  private pcLine!: THREE.Line;
  private pcDot!: THREE.Mesh;
  private pcAim = new THREE.Vector3(0, 1.4, -8);
  private ndc = new THREE.Vector2(0.25, -0.1);
  private sway = new THREE.Vector3(); // x = sideways, y = forward, z = turning; each from -1 to 1, smoothed
  private rigYaw = 0; // how far the body has turned (radians, left is positive)
  private auto: { x: number; z: number; yaw: number; pitch: number } | null = null;

  constructor(host: HTMLElement) {
    this.el = host;
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(host.clientWidth, host.clientHeight);
    this.renderer.xr.enabled = true;
    this.renderer.xr.setReferenceSpaceType('local-floor');
    this.renderer.xr.setFoveation?.(1);
    host.appendChild(this.renderer.domElement);
    // the ENTER VR button; on a screen that cannot do VR it is taken away instead of saying "not supported"
    const vrButton = VRButton.createButton(this.renderer);
    host.appendChild(vrButton);
    const noVr = () => (vrButton.style.display = 'none');
    const xrSystem = (navigator as Navigator & { xr?: { isSessionSupported(mode: string): Promise<boolean> } }).xr;
    if (!xrSystem) noVr();
    else
      xrSystem
        .isSessionSupported('immersive-vr')
        .then((ok) => {
          if (!ok) noVr();
        })
        .catch(noVr);

    // ?fov=58 narrows the PC view (the headset has its own)
    const fov = Number(new URLSearchParams(location.search).get('fov')) || 70;
    this.camera = new THREE.PerspectiveCamera(THREE.MathUtils.clamp(fov, 40, 90), host.clientWidth / host.clientHeight, 0.05, 600);
    this.camera.rotation.order = 'YXZ';
    this.camera.position.set(0, 1.6, 0);
    this.rig.add(this.camera);
    this.scene.add(this.rig);

    this.tooltip = makeLabel(' ', { h: 0.085, bg: 'rgba(8,12,28,0.94)', color: '#ffffff', onTop: true, px: 64, weight: '700' });
    this.tooltip.visible = false;
    this.scene.add(this.tooltip);

    this.fadeMesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.3, 16, 12),
      new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.BackSide, transparent: true, opacity: 0, depthTest: false })
    );
    this.fadeMesh.renderOrder = 1000;
    this.fadeMesh.visible = false;
    this.camera.add(this.fadeMesh);

    for (const i of [0, 1]) {
      const ray = this.renderer.xr.getController(i) as THREE.Object3D<any>;
      const hand = this.newHand(i, 'right', ray);
      this.rig.add(ray);
      // a drawn controller on each real one (the headset shows nothing of its own inside the room)
      const models = { left: makeController('left'), right: makeController('right') };
      models.left.group.visible = models.right.group.visible = false;
      ray.add(models.left.group, models.right.group);
      const model = () => (hand.side === 'left' ? models.left : models.right);
      this.xrModels.push(models.left, models.right);
      ray.addEventListener('connected', (e: any) => {
        hand.side = e.data?.handedness === 'left' ? 'left' : 'right';
        hand.line.visible = true;
        models.left.group.visible = hand.side === 'left';
        models.right.group.visible = hand.side !== 'left';
      });
      ray.addEventListener('disconnected', () => {
        hand.line.visible = false;
        models.left.group.visible = models.right.group.visible = false;
      });
      ray.addEventListener('selectstart', () => {
        model().press('trigger', true);
        this.trigger(hand);
      });
      ray.addEventListener('selectend', () => model().press('trigger', false));
      ray.addEventListener('squeezestart', () => {
        model().press('grip', true);
        this.squeeze(hand, true);
      });
      ray.addEventListener('squeezeend', () => {
        model().press('grip', false);
        this.squeeze(hand, false);
      });
      hand.line.visible = false;
      this.hands.push(hand);
    }
    const mray = new THREE.Object3D();
    this.scene.add(mray);
    this.mouse = this.newHand(2, 'mouse', mray);
    this.mouse.line.visible = false;
    this.hands.push(this.mouse);

    // ---- on a PC: two drawn controllers in front of the viewer; the right one follows the mouse
    this.pcRight = makeController('right');
    this.pcLeft = makeController('left');
    this.pcRight.group.position.set(0.2, -0.15, -0.46);
    this.pcLeft.group.position.set(-0.24, -0.175, -0.5);
    this.camera.add(this.pcRight.group, this.pcLeft.group);
    this.pcLine = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3(0, 0, -1)]),
      new THREE.LineBasicMaterial({ color: 0xbfe0ff, transparent: true, opacity: 0.9 })
    );
    this.pcLine.frustumCulled = false;
    this.pcDot = new THREE.Mesh(
      new THREE.RingGeometry(0.55, 1, 28),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.95, depthTest: false, side: THREE.DoubleSide })
    );
    this.pcDot.renderOrder = 998;
    this.scene.add(this.pcLine, this.pcDot);
    this.renderer.domElement.style.cursor = 'none';

    this.desktopControls();
    const onResize = () => {
      this.camera.aspect = host.clientWidth / host.clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(host.clientWidth, host.clientHeight);
    };
    window.addEventListener('resize', onResize);
    this.disposers.push(() => window.removeEventListener('resize', onResize));
    this.renderer.xr.addEventListener('sessionend', () => {
      this.camera.position.set(0, 1.6, 0);
    });

    this.renderer.setAnimationLoop(() => this.tick());
  }

  private newHand(id: number, side: Hand['side'], ray: THREE.Object3D): Hand {
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, -1)]),
      new THREE.LineBasicMaterial({ color: 0xbfe0ff, transparent: true, opacity: 0.9 })
    );
    line.scale.z = 6;
    ray.add(line);
    return {
      id,
      side,
      ray,
      line,
      hover: null,
      hoverPoint: new THREE.Vector3(),
      hoverDist: 0,
      grabbed: null,
      grabParent: null,
      tip: new THREE.Vector3(),
      vel: new THREE.Vector3(),
      speed: 0,
      squeezing: false,
      buttons: [],
      sliceCooldown: 0,
      aimed: null,
    };
  }

  get presenting(): boolean {
    return this.renderer.xr.isPresenting;
  }

  headPosition(out = new THREE.Vector3()): THREE.Vector3 {
    return this.camera.getWorldPosition(out);
  }

  register(obj: THREE.Object3D, it: Interact): void {
    obj.userData.it = it;
    this.targets.add(obj);
    if (it.slice) this.sliceables.add(obj);
  }

  /** Empties a group: frees what it held and forgets any pointing targets inside it. */
  clear(group: THREE.Object3D): void {
    group.traverse((o) => {
      if (o === group) return;
      this.targets.delete(o);
      this.sliceables.delete(o);
      this.billboards.delete(o);
      const m = o as THREE.Mesh;
      if (m.geometry) m.geometry.dispose();
      const mat = m.material as THREE.Material | THREE.Material[] | undefined;
      for (const x of Array.isArray(mat) ? mat : mat ? [mat] : []) {
        const map = (x as THREE.MeshBasicMaterial).map;
        if (map && !map.userData.shared) map.dispose();
        if (!x.userData.shared) x.dispose();
      }
    });
    for (const h of this.hands) {
      if (h.hover && isInside(h.hover, group)) h.hover = null;
      if (h.grabbed && isInside(h.grabbed, group)) h.grabbed = null;
    }
    group.clear();
  }

  /** Short dip to black; `mid` runs while the picture is dark (world switch, going inside). */
  fade(mid: () => void): void {
    this.fadeJob = { t: 0, mid, done: false };
    this.fadeMesh.visible = true;
  }

  moveTo(x: number, z: number): void {
    const head = this.headPosition(tmpV);
    this.rig.position.x += x - head.x;
    this.rig.position.z += z - head.z;
  }

  // ------------------------------------------------------------------ actions

  private trigger(hand: Hand): void {
    this.onAnyInput();
    const h = itOf(hand.hover);
    if (!h) return;
    if (h.it.select) h.it.select(hand);
    else if (h.it.slice) h.it.slice(hand);
  }

  private pressEnter(hand: Hand): void {
    const h = itOf(hand.hover);
    if (h?.it.enter) h.it.enter(hand);
    else this.onMenu();
  }

  private squeeze(hand: Hand, down: boolean): void {
    this.onAnyInput();
    hand.squeezing = down;
    if (down) {
      const other = this.hands.find((o) => o !== hand && o.grabbed);
      const h = this.grabbable(hand.hover);
      if (other && h && other.grabbed === h.root && h.it.grab?.scale) {
        this.twoHand = {
          obj: h.root,
          d0: Math.max(0.05, hand.ray.getWorldPosition(tmpV).distanceTo(other.ray.getWorldPosition(tmpV2))),
          s0: h.root.scale.x,
        };
        return;
      }
      if (!h || hand.grabbed) return;
      hand.grabbed = h.root;
      hand.grabParent = h.root.parent;
      hand.ray.attach(h.root);
      h.it.grab?.onGrab?.(hand);
      if (h.it.grab?.pull) {
        // it flies into the hand and stays just in front of it
        const obj = h.root;
        const from = obj.position.clone();
        // on a PC the ball waits a little further away, just above the drawn controller, so it does not fill the picture
        const to = hand.side === 'mouse' ? new THREE.Vector3(0.26, -0.17, -1.3) : new THREE.Vector3(0, 0.02, -0.32);
        this.pullJobs.push({ obj, from, to, t: 0, hand });
      }
    } else {
      if (this.twoHand && hand.grabbed !== this.twoHand.obj) {
        this.twoHand = null;
        return;
      }
      this.twoHand = null;
      const obj = hand.grabbed;
      if (!obj) return;
      hand.grabbed = null;
      this.setAim(hand, null);
      (hand.grabParent ?? this.scene).attach(obj);
      const it = obj.userData.it as Interact | undefined;
      const zone = this.aimedZone(hand, obj) ?? this.thrownZone(hand, obj) ?? this.nearZone(obj);
      if (zone) this.flyTo(obj, zone);
      else it?.grab?.onRelease?.(hand);
    }
  }

  private pullJobs: { obj: THREE.Object3D; from: THREE.Vector3; to: THREE.Vector3; t: number; hand: Hand }[] = [];

  private grabbable(obj: THREE.Object3D | null): { root: THREE.Object3D; it: Interact } | null {
    for (let o = obj; o; o = o.parent) {
      const it = o.userData.it as Interact | undefined;
      if (it?.grab) return { root: o, it };
    }
    return null;
  }

  /** The drop zone the hand points at (any distance), or null. */
  private aimedZone(hand: Hand, obj: THREE.Object3D): DropZone | null {
    const o = hand.ray.getWorldPosition(tmpV);
    const dir = tmpV2.set(0, 0, -1).applyQuaternion(hand.ray.getWorldQuaternion(tmpQ));
    let best: DropZone | null = null;
    let bestScore = 1;
    for (const z of this.zones) {
      if (!z.accepts(obj)) continue;
      const v = tmpV3.copy(z.center()).sub(o);
      const along = v.dot(dir);
      if (along < 0.4) continue;
      const off = v.addScaledVector(dir, -along).length();
      const score = off / Math.max(z.radius * 1.25, along * 0.11);
      if (score < bestScore) {
        best = z;
        bestScore = score;
      }
    }
    return best;
  }

  /** A real throw: the zone the hand was moving towards when it let go. */
  private thrownZone(hand: Hand, obj: THREE.Object3D): DropZone | null {
    if (hand.side === 'mouse' || hand.vel.length() < 1.3) return null;
    const p = obj.getWorldPosition(new THREE.Vector3());
    const dir = tmpV2.copy(hand.vel).normalize();
    let best: DropZone | null = null;
    let bestCos = Math.cos(THREE.MathUtils.degToRad(38));
    for (const z of this.zones) {
      if (!z.accepts(obj)) continue;
      const c = tmpV3.copy(z.center()).sub(p).normalize().dot(dir);
      if (c > bestCos) {
        best = z;
        bestCos = c;
      }
    }
    return best;
  }

  private nearZone(obj: THREE.Object3D): DropZone | null {
    const p = obj.getWorldPosition(new THREE.Vector3());
    let best: DropZone | null = null;
    let bestD = Infinity;
    for (const z of this.zones) {
      const d = z.center().distanceTo(p);
      if (d < z.radius && d < bestD && z.accepts(obj)) {
        best = z;
        bestD = d;
      }
    }
    return best;
  }

  /** Sends an object through the air, in an arc, into a drop zone. */
  flyTo(obj: THREE.Object3D, zone: DropZone): void {
    this.scene.attach(obj);
    const from = obj.position.clone();
    const dist = from.distanceTo(zone.center());
    this.flying.push({ obj, from, zone, t: 0, dur: THREE.MathUtils.clamp(0.25 + dist * 0.09, 0.35, 0.9), lift: THREE.MathUtils.clamp(dist * 0.22, 0.25, 1.4) });
  }

  private setAim(hand: Hand, zone: DropZone | null): void {
    if (hand.aimed === zone) return;
    hand.aimed?.highlight?.(false);
    hand.aimed = zone;
    zone?.highlight?.(true);
  }

  // ------------------------------------------------------------------ per frame

  private tick(): void {
    const dt = Math.min(this.clock.getDelta(), 0.05);
    const t = this.clock.elapsedTime;
    const xr = this.presenting;

    if (xr) this.pollGamepads(dt);
    else this.desktopMove(dt);
    this.glide(dt);
    if (!xr) {
      this.camera.rotation.set(this.pitch, this.yaw, 0);
      this.aimFromScreen();
    }

    // pointing
    const list: THREE.Object3D[] = [];
    for (const o of this.targets) if (shown(o)) list.push(o);
    let tipHand: Hand | null = null;
    for (const hand of this.hands) {
      const active = hand.side === 'mouse' ? !xr : xr && hand.line.visible;
      if (!active) {
        this.setHover(hand, null);
        continue;
      }
      hand.ray.getWorldPosition(tmpV);
      hand.ray.getWorldQuaternion(tmpQ);
      const dir = tmpV2.set(0, 0, -1).applyQuaternion(tmpQ);
      const tipNow = tmpV3.copy(tmpV).addScaledVector(dir, 0.4);
      const inv = 1 / Math.max(dt, 0.001);
      hand.vel.lerp(new THREE.Vector3().subVectors(tipNow, hand.tip).multiplyScalar(inv), 0.45);
      hand.speed = hand.vel.length();
      hand.tip.copy(tipNow);
      hand.sliceCooldown -= dt;

      if (hand.grabbed) {
        this.setHover(hand, null);
        const zone = this.aimedZone(hand, hand.grabbed);
        this.setAim(hand, zone);
        hand.line.scale.z = zone ? zone.center().distanceTo(hand.ray.getWorldPosition(tmpV)) : 6;
        (hand.line.material as THREE.LineBasicMaterial).color.setHex(zone ? 0x6ee7b7 : 0xbfe0ff);
        continue;
      }
      (hand.line.material as THREE.LineBasicMaterial).color.setHex(0xbfe0ff);
      this.raycaster.set(tmpV, dir);
      this.raycaster.far = 80;
      const hit = this.raycaster.intersectObjects(list, true)[0];
      if (hit) {
        hand.hoverPoint.copy(hit.point);
        hand.hoverDist = hit.distance;
        this.setHover(hand, hit.object);
        hand.line.scale.z = hit.distance;
      } else {
        this.setHover(hand, null);
        hand.line.scale.z = 6;
      }
      if (hand.hover && !tipHand) tipHand = hand;

      // cutting by a fast swing with the controller's tip inside the object
      if (hand.side !== 'mouse' && hand.speed > 1.6 && hand.sliceCooldown <= 0) {
        for (const s of this.sliceables) {
          if (!shown(s)) continue;
          tmpBox.setFromObject(s).expandByScalar(0.08);
          if (tmpBox.containsPoint(hand.tip)) {
            hand.sliceCooldown = 0.8;
            (s.userData.it as Interact).slice?.(hand);
            break;
          }
        }
      }
    }

    // a pulled object arriving in the hand
    for (let i = this.pullJobs.length - 1; i >= 0; i--) {
      const j = this.pullJobs[i];
      if (j.hand.grabbed !== j.obj) {
        this.pullJobs.splice(i, 1);
        continue;
      }
      j.t += dt;
      const k = Math.min(j.t / 0.26, 1);
      j.obj.position.lerpVectors(j.from, j.to, 1 - Math.pow(1 - k, 3));
      if (k >= 1) this.pullJobs.splice(i, 1);
    }

    // objects in the air on their way to a zone
    for (let i = this.flying.length - 1; i >= 0; i--) {
      const f = this.flying[i];
      f.t += dt;
      const k = Math.min(f.t / f.dur, 1);
      f.obj.position.lerpVectors(f.from, f.zone.center(), k);
      f.obj.position.y += Math.sin(k * Math.PI) * f.lift;
      if (k >= 1) {
        this.flying.splice(i, 1);
        f.zone.drop(f.obj);
      }
    }

    // two-hand resize
    if (this.twoHand) {
      const hs = this.hands.filter((h) => h.squeezing && h.side !== 'mouse');
      if (hs.length === 2) {
        const d = hs[0].ray.getWorldPosition(tmpV).distanceTo(hs[1].ray.getWorldPosition(tmpV2));
        const s = THREE.MathUtils.clamp((this.twoHand.s0 * d) / this.twoHand.d0, 0.3, 4);
        this.twoHand.obj.scale.setScalar(s);
      }
    }

    // tooltip
    const tip = tipHand ? itOf(tipHand.hover)?.it.tip : undefined;
    if (tipHand && tip) {
      setLabel(this.tooltip, typeof tip === 'function' ? tip() : tip);
      const head = this.headPosition(tmpV);
      const dist = head.distanceTo(tipHand.hoverPoint);
      const k = THREE.MathUtils.clamp(dist * 0.36, 0.5, 16);
      this.tooltip.scale.set(this.tooltip.userData.w * k, this.tooltip.userData.hgt * k, 1);
      this.tooltip.position.copy(tipHand.hoverPoint).addScaledVector(tmpV2.copy(head).sub(tipHand.hoverPoint).normalize(), Math.min(0.3, dist * 0.3));
      this.tooltip.position.y += 0.12 * k;
      this.tooltip.quaternion.copy(this.camera.getWorldQuaternion(tmpQ));
      this.tooltip.visible = true;
    } else {
      this.tooltip.visible = false;
    }

    // things that always face the viewer
    if (this.billboards.size) {
      const head = this.headPosition(tmpV);
      for (const b of this.billboards) {
        b.getWorldPosition(tmpV2);
        const yaw = Math.atan2(head.x - tmpV2.x, head.z - tmpV2.z);
        b.rotation.set(0, yaw - parentYaw(b), 0);
      }
    }

    // fade
    if (this.fadeJob) {
      const f = this.fadeJob;
      f.t += dt;
      const half = 0.3;
      const mat = this.fadeMesh.material as THREE.MeshBasicMaterial;
      if (f.t < half) mat.opacity = f.t / half;
      else {
        if (!f.done) {
          f.done = true;
          f.mid();
        }
        mat.opacity = Math.max(0, 1 - (f.t - half) / half);
        if (f.t >= half * 2) {
          this.fadeJob = null;
          this.fadeMesh.visible = false;
        }
      }
    }

    for (const f of this.frame) f(dt, t);
    if (!xr) this.camera.rotation.set(this.pitch, this.yaw, 0);
    this.drawPcHands(dt, t, xr);
    for (const m of this.xrModels) m.update(dt);
    this.renderer.render(this.scene, this.camera);
  }

  /** On a PC: the right controller points where the mouse points, with its ray and a small ring on the target. */
  private drawPcHands(dt: number, t: number, xr: boolean): void {
    const on = !xr;
    this.pcRight.group.visible = this.pcLeft.group.visible = this.pcLine.visible = this.pcDot.visible = on;
    if (!on) return;
    this.camera.updateMatrixWorld();
    const m = this.mouse;
    const origin = m.ray.getWorldPosition(tmpV);
    const dir = tmpV2.set(0, 0, -1).applyQuaternion(m.ray.getWorldQuaternion(tmpQ));
    const zone = m.grabbed ? m.aimed : null;
    const target = zone ? zone.center() : m.hover ? tmpV3.copy(m.hoverPoint) : tmpV3.copy(origin).addScaledVector(dir, 9);
    this.pcAim.lerp(target, 1 - Math.exp(-dt * 18));

    // The hands are never perfectly still, and they lean a little into the movement: sideways gliding and turning
    // roll and turn them gently towards where the body is going, walking forward tips them slightly.
    const a = 1 - Math.exp(-dt * 5);
    this.sway.x += (THREE.MathUtils.clamp(this.move.x / 2, -1, 1) - this.sway.x) * a;
    this.sway.y += (THREE.MathUtils.clamp(this.move.y / 2, -1, 1) - this.sway.y) * a;
    this.sway.z += (THREE.MathUtils.clamp(this.turn / 0.9, -1, 1) - this.sway.z) * a;
    const { x: sx, y: sy, z: st } = this.sway;
    const lean = (o: THREE.Object3D) => {
      o.rotateY(-sx * 0.1 + st * 0.12);
      o.rotateZ(-sx * 0.12 + st * 0.1);
      o.rotateX(-Math.abs(sy) * 0.05);
    };
    const g = this.pcRight.group;
    g.position.set(0.2 + Math.sin(t * 0.9) * 0.004 + sx * 0.014 - st * 0.012, -0.15 + Math.sin(t * 1.3) * 0.004 - Math.abs(sy) * 0.005, -0.46);
    g.lookAt(this.pcAim);
    g.rotateY(Math.PI);
    lean(g);
    const l = this.pcLeft.group;
    l.position.set(-0.24 + sx * 0.014 - st * 0.012, -0.175 + Math.sin(t * 1.1 + 1) * 0.004 - Math.abs(sy) * 0.005, -0.5);
    l.rotation.set(0.12 + Math.sin(t * 0.7) * 0.01, 0.22, 0);
    lean(l);
    this.pcLeft.stick((this.keys.has('d') ? 1 : 0) - (this.keys.has('a') ? 1 : 0), (this.keys.has('w') ? 1 : 0) - (this.keys.has('s') ? 1 : 0));
    this.pcRight.stick((this.keys.has('e') ? 1 : 0) - (this.keys.has('q') ? 1 : 0), 0);
    this.pcRight.update(dt);
    this.pcLeft.update(dt);

    g.updateMatrixWorld();
    const from = g.getWorldPosition(tmpV);
    const pos = this.pcLine.geometry.getAttribute('position') as THREE.BufferAttribute;
    pos.setXYZ(0, from.x, from.y, from.z);
    pos.setXYZ(1, this.pcAim.x, this.pcAim.y, this.pcAim.z);
    pos.needsUpdate = true;
    (this.pcLine.material as THREE.LineBasicMaterial).color.setHex(zone ? 0x6ee7b7 : 0xbfe0ff);

    const head = this.headPosition(tmpV2);
    const d = head.distanceTo(this.pcAim);
    this.pcDot.position.copy(this.pcAim);
    this.pcDot.quaternion.copy(this.camera.getWorldQuaternion(tmpQ));
    this.pcDot.scale.setScalar(d * (m.hover || zone ? 0.011 : 0.006));
    (this.pcDot.material as THREE.MeshBasicMaterial).opacity = m.hover || zone ? 0.95 : 0.5;
  }

  private setHover(hand: Hand, obj: THREE.Object3D | null): void {
    const a = itOf(hand.hover);
    const b = itOf(obj);
    hand.hover = obj;
    if (a?.root === b?.root) return;
    const stillHovered = (root: THREE.Object3D) => this.hands.some((h) => h !== hand && itOf(h.hover)?.root === root);
    if (a && !stillHovered(a.root)) a.it.hover?.(false);
    if (b) b.it.hover?.(true);
  }

  // ------------------------------------------------------------------ movement

  private wantMove = new THREE.Vector2();
  private wantTurn = 0;

  /** Eases towards the wanted speed and turn, so starting and stopping are never abrupt. */
  private glide(dt: number): void {
    const a = 1 - Math.exp(-dt * 3.2);
    this.move.lerp(this.wantMove, a);
    this.turn += (this.wantTurn - this.turn) * (1 - Math.exp(-dt * 4));
    if (Math.abs(this.turn) > 0.002) {
      const head = this.headPosition(tmpV);
      const ang = this.turn * dt;
      this.rig.position.sub(head).applyAxisAngle(UP, ang).add(head);
      this.rig.rotateOnWorldAxis(UP, ang);
      this.rigYaw += ang;
    }
    if (this.move.lengthSq() > 0.00002) {
      const fwd = this.camera.getWorldDirection(tmpV2);
      fwd.y = 0;
      if (fwd.lengthSq() < 0.0001) return;
      fwd.normalize();
      const right = tmpV3.set(-fwd.z, 0, fwd.x);
      const nx = this.rig.position.x + (fwd.x * this.move.y + right.x * this.move.x) * dt;
      const nz = this.rig.position.z + (fwd.z * this.move.y + right.z * this.move.x) * dt;
      const head = this.headPosition(tmpV);
      const hx = head.x + (nx - this.rig.position.x);
      const hz = head.z + (nz - this.rig.position.z);
      if (Math.hypot(hx, hz) <= this.walkRadius) {
        this.rig.position.x = nx;
        this.rig.position.z = nz;
      } else {
        this.move.multiplyScalar(0.5);
      }
    }
  }

  private pollGamepads(dt: number): void {
    const session = this.renderer.xr.getSession();
    this.wantMove.set(0, 0);
    this.wantTurn = 0;
    if (!session) return;
    const dead = (v: number) => (Math.abs(v) < 0.15 ? 0 : (v - Math.sign(v) * 0.15) / 0.85);
    for (const src of session.inputSources) {
      const gp = src.gamepad;
      if (!gp) continue;
      const hand = this.hands.find((h) => h.side === src.handedness) ?? this.hands[0];
      const ax = dead(gp.axes.length >= 4 ? gp.axes[2] : (gp.axes[0] ?? 0));
      const ay = dead(gp.axes.length >= 4 ? gp.axes[3] : (gp.axes[1] ?? 0));

      if (hand.grabbed && !(hand.grabbed.userData.it as Interact | undefined)?.grab?.pull) {
        // holding a board or a planet: the stick pushes it away or pulls it closer
        hand.grabbed.position.z = THREE.MathUtils.clamp(hand.grabbed.position.z + ay * 3 * dt, -14, -0.4);
        if (src.handedness !== 'left') this.wantTurn = -ax * this.turnSpeed;
      } else if (src.handedness === 'left') {
        this.wantMove.set(ax * this.glideSpeed * 0.8, -ay * this.glideSpeed);
      } else {
        this.wantTurn = -ax * this.turnSpeed;
      }

      const was = hand.buttons;
      const now = gp.buttons.map((b) => b.pressed);
      if (now[4] && !was[4]) {
        this.onAnyInput();
        this.pressEnter(hand);
      }
      if (now[5] && !was[5]) {
        this.onAnyInput();
        this.onBack();
      }
      hand.buttons = now;
    }
  }

  // ------------------------------------------------------------------ mouse and keyboard

  private desktopControls(): void {
    const dom = this.renderer.domElement;
    let downX = 0;
    let downY = 0;
    let dragging = false;
    let moved = false;
    const aimMouse = (e: PointerEvent | WheelEvent | MouseEvent) => {
      const r = dom.getBoundingClientRect();
      this.ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      this.aimFromScreen();
    };
    const down = (e: PointerEvent) => {
      if (this.presenting) return;
      aimMouse(e);
      if (e.button === 2) {
        this.pcRight.press('grip', true);
        this.squeeze(this.mouse, true);
        return;
      }
      this.pcRight.press('trigger', true);
      dragging = true;
      moved = false;
      downX = e.clientX;
      downY = e.clientY;
    };
    const move = (e: PointerEvent) => {
      if (this.presenting) return;
      if (dragging && !this.mouse.grabbed) {
        const dx = e.clientX - downX;
        const dy = e.clientY - downY;
        if (moved || Math.abs(dx) + Math.abs(dy) > 5) {
          moved = true;
          this.yaw += (e.movementX || 0) * 0.004;
          this.pitch = THREE.MathUtils.clamp(this.pitch + (e.movementY || 0) * 0.004, -1.3, 1.3);
        }
      }
      aimMouse(e);
    };
    const up = (e: PointerEvent) => {
      if (this.presenting) return;
      if (e.button === 2) {
        this.pcRight.press('grip', false);
        this.squeeze(this.mouse, false);
        return;
      }
      this.pcRight.press('trigger', false);
      if (dragging && !moved) this.trigger(this.mouse);
      dragging = false;
    };
    const wheel = (e: WheelEvent) => {
      const g = this.mouse.grabbed;
      if (!g || this.presenting) return;
      e.preventDefault();
      if (e.shiftKey) g.scale.multiplyScalar(e.deltaY < 0 ? 1.08 : 0.92);
      else g.position.z += e.deltaY < 0 ? -0.25 : 0.25;
    };
    const key = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement | null)?.tagName === 'INPUT') return;
      const k = e.key.toLowerCase();
      this.keys.add(k);
      if (this.presenting) return;
      if (k === 'b' || k === 'backspace') this.onBack();
      if (k === 'm') this.onMenu();
      if (k === 'f' || k === 'enter') this.pressEnter(this.mouse);
      if (k === 'x') itOf(this.mouse.hover)?.it.slice?.(this.mouse);
      const g = this.mouse.grabbed;
      if (g && (k === '[' || k === ']')) g.rotateY(k === '[' ? 0.25 : -0.25);
    };
    const keyUp = (e: KeyboardEvent) => this.keys.delete(e.key.toLowerCase());
    const noMenu = (e: Event) => e.preventDefault();
    dom.addEventListener('pointerdown', down);
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
    dom.addEventListener('wheel', wheel, { passive: false });
    dom.addEventListener('contextmenu', noMenu);
    window.addEventListener('keydown', key);
    window.addEventListener('keyup', keyUp);
    this.disposers.push(() => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      window.removeEventListener('keydown', key);
      window.removeEventListener('keyup', keyUp);
    });
  }

  /** Points the mouse hand from the eye through the place on the screen where the mouse is. */
  private aimFromScreen(): void {
    this.camera.updateMatrixWorld();
    this.raycaster.setFromCamera(this.ndc, this.camera);
    this.mouse.ray.position.copy(this.raycaster.ray.origin);
    this.mouse.ray.quaternion.setFromUnitVectors(tmpV.set(0, 0, -1), this.raycaster.ray.direction);
    this.mouse.ray.updateMatrixWorld();
  }

  /** PC only: walk by itself to a spot and a direction (degrees, 0 = straight ahead, 90 = to the right), slowly. */
  walkTo(x: number, z: number, headingDeg: number, pitch = 0): void {
    this.auto = { x, z, yaw: -THREE.MathUtils.degToRad(headingDeg), pitch };
  }

  private desktopMove(dt: number): void {
    const f = (this.keys.has('w') ? 1 : 0) - (this.keys.has('s') ? 1 : 0);
    const s = (this.keys.has('d') ? 1 : 0) - (this.keys.has('a') ? 1 : 0);
    const r = (this.keys.has('q') ? 1 : 0) - (this.keys.has('e') ? 1 : 0);
    if (this.auto && (f || s || r)) this.auto = null; // the keys always win
    if (this.auto) {
      const a = this.auto;
      // the look offset made with the mouse melts away, the body does the turning
      this.yaw += (0 - this.yaw) * (1 - Math.exp(-dt * 2.5));
      this.pitch += (a.pitch - this.pitch) * (1 - Math.exp(-dt * 2.2));
      let dy = a.yaw - (this.rigYaw + this.yaw);
      dy = Math.atan2(Math.sin(dy), Math.cos(dy));
      const head = this.headPosition(tmpV);
      const ex = a.x - head.x;
      const ez = a.z - head.z;
      const fwd = this.camera.getWorldDirection(tmpV2);
      fwd.y = 0;
      fwd.normalize();
      const along = ex * fwd.x + ez * fwd.z;
      const side = ex * -fwd.z + ez * fwd.x;
      const v = this.glideSpeed * 1.25;
      const w = this.turnSpeed * 1.15;
      this.wantMove.set(THREE.MathUtils.clamp(side * 1.3, -v, v), THREE.MathUtils.clamp(along * 1.3, -v, v));
      this.wantTurn = THREE.MathUtils.clamp(dy * 1.7, -w, w);
      if (Math.hypot(ex, ez) < 0.04 && Math.abs(dy) < 0.006 && Math.abs(a.pitch - this.pitch) < 0.004) {
        this.auto = null;
        this.wantMove.set(0, 0);
        this.wantTurn = 0;
      }
      return;
    }
    this.wantMove.set(s * this.glideSpeed * 1.6, f * this.glideSpeed * 1.6);
    this.wantTurn = r * this.turnSpeed * 1.5;
  }

  /** Test helper for the PC: look in a direction (radians). */
  look(yaw: number, pitch = 0): void {
    this.yaw = yaw;
    this.pitch = pitch;
  }

  dispose(): void {
    this.renderer.setAnimationLoop(null);
    for (const d of this.disposers) d();
    this.renderer.dispose();
    this.el.replaceChildren();
  }
}

function isInside(obj: THREE.Object3D, group: THREE.Object3D): boolean {
  for (let o: THREE.Object3D | null = obj; o; o = o.parent) if (o === group) return true;
  return false;
}

const pyQ = new THREE.Quaternion();
const pyE = new THREE.Euler();
function parentYaw(obj: THREE.Object3D): number {
  if (!obj.parent) return 0;
  obj.parent.getWorldQuaternion(pyQ);
  return pyE.setFromQuaternion(pyQ, 'YXZ').y;
}
