// Puts the whole room together: the space deck, the boards, the stations, the showpieces, the guide, the menu.
//
// Around the viewer (0 degrees = straight ahead, 90 = to the right), with room to walk between them:
//   boards -44 / 0 / 44 · basket 84 · shelf of balls 124 · scales 164 · bin 188 · guessing game 212 ·
//   the loaf to cut 236 · the guide 292
// Saturn hangs far ahead, high, and the region planets are in orbit.

import * as THREE from 'three';

import { Board } from './board';
import { type Cube, type Dim } from './data';
import { Engine } from './engine';
import { floorCompass, GuessGame, InsideWall, makeBin, Planets, Saturn, Watch } from './extras';
import { AskPanel, Guide, Menu, Welcome, type AskAgent } from './people';
import { Basket, Scales, Shelf, Slicer } from './stations';
import { Store } from './store';
import { place, runTweens } from './ui';
import { buildSpace, type World } from './worlds';

const LAYOUT_KEY = 'vrdash.layout.v4';

interface SavedBoard {
  id: string;
  dim: Dim;
  p: number[];
  q: number[];
  s: number;
}

function load<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}
function save(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* private mode or a full store: the room still works, it just is not remembered */
  }
}

export interface AppOptions {
  /** One line under the title of the welcome board: where the numbers come from. */
  source: string;
  /** Asks the Fabric data agent. Missing = the guide says the agent is not connected. */
  ask?: AskAgent;
  onHud(text: string): void;
}

export class VrApp {
  readonly engine: Engine;
  readonly store: Store;
  private world: World;
  private room = new THREE.Group();
  private boards: Board[] = [];
  private watch: Watch;
  private menu: Menu;
  private welcome: Welcome;
  private nextId = 1;
  /** The stations, exposed for the local test page. */
  parts: Record<string, unknown> = {};

  constructor(
    host: HTMLElement,
    cube: Cube,
    private opts: AppOptions
  ) {
    const engine = (this.engine = new Engine(host));
    const store = (this.store = new Store(cube));

    this.world = buildSpace();
    engine.scene.add(this.world.group);
    engine.scene.add(this.room);

    // ---- the stations
    const shelf = new Shelf(engine, store);
    place(shelf.group, 124, 6.2);
    shelf.group.scale.setScalar(1.25);
    const basket = new Basket(engine, store, shelf);
    place(basket.group, 84, 5.4);
    const scales = new Scales(engine, store, shelf);
    place(scales.group, 164, 5.6);
    const slicer = new Slicer(engine, store);
    // far enough round that the guide's question buttons do not stand in front of it
    place(slicer.group, 236, 6.0);
    const guess = new GuessGame(engine, store);
    place(guess.group, 212, 5.8);
    const ask = { panel: undefined as AskPanel | undefined };
    const guide = new Guide(engine, store, () => ask.panel?.show(true));
    place(guide.group, 292, 3.9);
    ask.panel = new AskPanel(engine, guide, opts.ask);
    engine.scene.add(ask.panel.group);
    const bin = makeBin();
    place(bin, 188, 6.6);
    engine.billboards.add(bin.userData.labelHolder as THREE.Object3D);
    this.room.add(shelf.group, basket.group, scales.group, slicer.group, guess.group, guide.group, bin);
    engine.zones.push({
      center: () => bin.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.7, 0)),
      radius: 1.0,
      accepts: (o) => !!o.userData.board,
      drop: (o) => this.removeBoard(o.userData.board as Board),
      highlight: (on) => ((bin.userData.ring as THREE.Object3D).visible = on),
    });

    const names: [string, number][] = [
      ['BOARDS', 0],
      ['BASKET', 84],
      ['SHELF', 124],
      ['SCALES', 164],
      ['BIN', 188],
      ['GUESS', 212],
      ['CUT IT', 236],
      ['ASK SHAI', 292],
    ];
    this.world.group.add(floorCompass(names, '#9fd8ff'));

    // ---- the showpieces
    this.world.group.add(new Saturn(engine, store).group, new Planets(engine, store).group);

    const wall = new InsideWall(store);
    engine.scene.add(wall.group);
    this.watch = new Watch(engine, store);
    this.welcome = new Welcome(engine, opts.source);
    engine.scene.add(this.welcome.group);
    this.menu = new Menu(engine, store, {
      resetRoom: () => this.resetRoom(),
      addBoard: (d) => this.addBoardInFront(d),
      help: () => {
        this.menu.toggle(false);
        this.welcome.show(true);
      },
    });
    engine.scene.add(this.menu.group);

    this.restoreBoards();
    this.parts = { shelf, basket, scales, slicer, guess, guide, menu: this.menu, ask: ask.panel, welcome: this.welcome };

    engine.onMenu = () => this.menu.toggle();
    engine.onBack = () => {
      if (ask.panel?.group.visible) ask.panel.show(false);
      else if (this.menu.group.visible) this.menu.toggle(false);
      else if (!store.back()) guide.say('Nothing to go back to: you are looking at everything.');
    };
    // ---- a guided walk on a PC (?tour=1): number keys take the viewer to a spot in front of each station
    if (new URLSearchParams(location.search).get('tour')) {
      const at = (deg: number, r: number): [number, number] => {
        const a = THREE.MathUtils.degToRad(deg);
        return [Math.sin(a) * r, -Math.cos(a) * r];
      };
      const stops: Record<string, [number, number, number, number]> = {
        '1': [0, 0, 0, 0.06], // the three boards
        '2': [0, 0, 0, 0.4], // Saturn and the ring of months
        '3': [...at(-44, 1.4), -44, 0.05], // the region board
        '4': [...at(104, 1.0), 104, -0.02], // basket and shelf
        '5': [...at(150, 1.2), 150, 0.0], // shelf and scales
        '6': [...at(212, 1.8), 212, 0.02], // guessing game
        '7': [...at(236, 2.4), 236, 0.1], // the cut
        '8': [...at(292, 0.5), 286, 0.0], // the guide
        '9': [0, 0, 44, 0.05], // the product board
        '0': [0, 0, 0, 0.14], // back to the middle, looking a little up
      };
      window.addEventListener('keydown', (e) => {
        if ((e.target as HTMLElement | null)?.tagName === 'INPUT') return;
        const s = stops[e.key];
        if (s) engine.walkTo(s[0], s[1], s[2], s[3]);
      });
    }

    store.subscribe(() => this.onChange());
    engine.frame.push((dt, t) => {
      runTweens(dt);
      this.world.update(dt, t);
    });
    engine.walkRadius = this.world.radius;
    this.onChange();
  }

  private onChange(): void {
    for (const b of this.boards) b.render();
    const { cube, filter, measure } = this.store;
    const y = cube.yoy(filter, measure);
    const what = Object.keys(filter).filter((k) => k !== 'year').length ? 'what you filtered' : 'all of Aurora';
    this.world.setAmbient(y.pct, what);
    this.opts.onHud(this.watch.text());
  }

  // ------------------------------------------------------------------ boards ("your room")

  private newBoard(dim: Dim, id = `b${this.nextId++}`): Board {
    const b = new Board(this.engine, this.store, dim, id, () => this.saveBoards());
    this.boards.push(b);
    this.room.add(b.group);
    return b;
  }

  private defaultBoards(): void {
    const spec: [Dim, number][] = [
      ['region', -44],
      ['month', 0],
      ['product', 44],
    ];
    for (const [dim, angle] of spec) {
      const b = this.newBoard(dim);
      b.group.scale.setScalar(1.3);
      place(b.group, angle, 6.4, (b.H / 2) * 1.3 + 0.5);
    }
  }

  private restoreBoards(): void {
    const saved = load<SavedBoard[]>(LAYOUT_KEY);
    if (!saved || !Array.isArray(saved) || !saved.length) {
      this.defaultBoards();
      return;
    }
    for (const s of saved) {
      const b = this.newBoard(s.dim, s.id);
      b.group.position.fromArray(s.p);
      b.group.quaternion.fromArray(s.q);
      b.group.scale.setScalar(s.s || 1);
      const n = Number(String(s.id).slice(1));
      if (n >= this.nextId) this.nextId = n + 1;
    }
  }

  private saveBoards(): void {
    save(
      LAYOUT_KEY,
      this.boards.map((b) => ({
        id: b.id,
        dim: b.dim,
        p: b.group.position.toArray(),
        q: b.group.quaternion.toArray(),
        s: b.group.scale.x,
      }))
    );
  }

  private removeBoard(b: Board): void {
    this.engine.targets.delete(b.group);
    this.engine.clear(b.group);
    b.group.removeFromParent();
    this.boards = this.boards.filter((x) => x !== b);
    this.saveBoards();
  }

  private addBoardInFront(dim: Dim): void {
    const b = this.newBoard(dim);
    const head = this.engine.headPosition();
    const dir = new THREE.Vector3(0, 0, -1).applyQuaternion(this.engine.camera.getWorldQuaternion(new THREE.Quaternion()));
    dir.y = 0;
    dir.normalize();
    b.group.position.copy(head).addScaledVector(dir, 4.2);
    b.group.position.y = b.H / 2 + 0.55;
    b.group.rotation.set(0, Math.atan2(-dir.x, -dir.z), 0);
    this.menu.toggle(false);
    this.saveBoards();
  }

  private resetRoom(): void {
    for (const b of [...this.boards]) this.removeBoard(b);
    this.defaultBoards();
    this.saveBoards();
    this.menu.toggle(false);
  }

  dispose(): void {
    this.engine.dispose();
  }
}
