// The page: loads Aurora once, then hands the screen to the VR room. Shows an honest state while loading or on failure.

import { useEffect, useRef, useState } from 'react';

import { VrApp } from './vr/app';
import type { Cube } from './vr/data';
import type { AskAgent } from './vr/people';
import { fontsReady } from './vr/text';

type State = { kind: 'loading' } | { kind: 'error'; message: string } | { kind: 'ready'; rows: number };

const box: React.CSSProperties = {
  position: 'absolute',
  top: 12,
  left: 12,
  padding: '10px 14px',
  borderRadius: 10,
  background: 'rgba(8,12,28,0.8)',
  border: '1px solid #2a3a7a',
  color: '#dbe5ff',
  font: '13px/1.5 "Segoe UI", system-ui, sans-serif',
  pointerEvents: 'none',
  whiteSpace: 'pre-line',
  maxWidth: 360,
};

export function VrRoom({ loadCube, source, ask }: { loadCube: () => Promise<Cube>; source: string; ask?: AskAgent }) {
  const host = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<State>({ kind: 'loading' });
  const [hud, setHud] = useState('');
  // H hides or shows the corner box (for a clean picture). ?hud=0 in the address starts without it.
  const [showHud, setShowHud] = useState(() => new URLSearchParams(location.search).get('hud') !== '0');
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement | null)?.tagName === 'INPUT') return;
      if (e.key.toLowerCase() === 'h') setShowHud((v) => !v);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    let app: VrApp | undefined;
    let cancelled = false;
    Promise.all([loadCube(), fontsReady()])
      .then(([cube]) => {
        if (cancelled || !host.current) return;
        app = new VrApp(host.current, cube, { source, ask, onHud: setHud });
        (window as unknown as { vr?: VrApp }).vr = app;
        setState({ kind: 'ready', rows: cube.rows.length });
      })
      .catch((err: unknown) => {
        if (!cancelled) setState({ kind: 'error', message: err instanceof Error ? err.message : String(err) });
      });
    return () => {
      cancelled = true;
      app?.dispose();
    };
  }, [loadCube, source, ask]);

  return (
    <div style={{ position: 'fixed', inset: 0, background: '#05060f', touchAction: 'none', overflow: 'hidden' }}>
      <div ref={host} style={{ position: 'absolute', inset: 0 }} />
      {(showHud || state.kind !== 'ready') && (
      <div style={box}>
        <div style={{ fontWeight: 700, marginBottom: 2 }}>Aurora VR room</div>
        {state.kind === 'loading' && <div>Asking the Aurora Sales model…</div>}
        {state.kind === 'error' && (
          <div style={{ color: '#fca5a5' }}>
            Could not read the Aurora Sales model.{'\n'}
            {state.message}
          </div>
        )}
        {state.kind === 'ready' && (
          <>
            <div style={{ color: '#8fa0c8' }}>
              {source} · {state.rows.toLocaleString('en-US')} rows
            </div>
            <div style={{ marginTop: 4 }}>{hud}</div>
            <div style={{ marginTop: 6, color: '#8fa0c8' }}>
              On a PC: click = trigger · hold right button = grab (then point and let go) · drag = look · W A S D =
              glide · Q E = turn · F = go inside · B = back · M = menu · H = hide this box
            </div>
          </>
        )}
      </div>
      )}
    </div>
  );
}
