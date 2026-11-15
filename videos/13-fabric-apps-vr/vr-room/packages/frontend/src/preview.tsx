// Local look at the room without the Fabric sign-in gate (dev server only: /preview.html is not part of the build).
// It reads a saved copy of the same query result, so the numbers are real but not live.
// Test hooks in the address: ?yaw=90&pitch=-10&x=0&z=0&scene=basket,scales,slice2,inside,filter,menu,guess
import { createRoot } from 'react-dom/client';

import sample from './dev/cube.sample.json';
import type { VrApp } from './vr/app';
import { cubeFromTable } from './vr/data';
import { VrRoom } from './VrRoom';

const load = async () => cubeFromTable(sample.columns as string[], sample.rows as unknown[][]);

// a stand-in for the data agent, so the ask panel can be tried locally
const fakeAsk = async (q: string) => {
  await new Promise((r) => setTimeout(r, 1200));
  return `(local preview: no agent here) You asked: ${q}`;
};

createRoot(document.getElementById('root')!).render(<VrRoom loadCube={load} source="Saved copy of the model (local preview)" ask={fakeAsk} />);

const q = new URLSearchParams(location.search);
const wait = setInterval(() => {
  const vr = (window as unknown as { vr?: VrApp }).vr;
  if (!vr) return;
  clearInterval(wait);
  /* eslint-disable @typescript-eslint/no-explicit-any */
  const parts = vr.parts as any;
  const token = (label: string) => parts.shelf.tokens.find((t: any) => t.userData.token.label === label);
  if (q.get('aim')) {
    // ?aim=0.62,0.5 = where the mouse points, as a share of the window
    const [ax, ay] = q.get('aim')!.split(',').map(Number);
    window.dispatchEvent(new PointerEvent('pointermove', { clientX: innerWidth * ax, clientY: innerHeight * ay }));
  }
  // ?keys=d holds keys down (to see the room while gliding or turning)
  for (const k of (q.get('keys') ?? '').split('').filter(Boolean)) window.dispatchEvent(new KeyboardEvent('keydown', { key: k }));
  for (const s of (q.get('scene') ?? '').split(',')) {
    if (s === 'basket') for (const l of ['Revenue', 'Europe', 'Asia Pacific', 'vs last year']) parts.basket.add(token(l));
    if (s === 'scales') {
      parts.scales.put(0, token('North America'));
      parts.scales.put(1, token('Latin America'));
    }
    if (s === 'slice1' || s === 'slice2') parts.slicer.slice();
    if (s === 'slice2') parts.slicer.slice({ dim: 'region', value: 'Europe' });
    if (s === 'inside') vr.store.enter('region', 'Europe');
    if (s === 'filter') vr.store.toggle('category', 'Camping');
    if (s === 'menu') setTimeout(() => parts.menu.toggle(true), 400);
    if (s === 'ask') setTimeout(() => parts.ask.show(true), 400);
    if (s === 'start') parts.welcome.group.visible = false;
    if (s === 'guess') {
      parts.guess.guess = parts.guess.max * 0.4;
      parts.guess.paint();
      parts.guess.reveal();
    }
  }
  setTimeout(() => {
    if (q.get('x') || q.get('z')) vr.engine.moveTo(Number(q.get('x') ?? 0), Number(q.get('z') ?? 0));
    vr.engine.look((-Number(q.get('yaw') ?? 0) * Math.PI) / 180, (Number(q.get('pitch') ?? 0) * Math.PI) / 180);
  }, 100);
}, 50);
