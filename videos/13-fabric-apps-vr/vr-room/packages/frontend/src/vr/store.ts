// The one shared "what am I looking at" state: the filter, with an undo stack.

import type { Cube, Dim, Filter } from './data';

type Listener = () => void;

export class Store {
  filter: Filter = {};
  /** What the bars, planets and dunes measure (additive measures only). */
  measure: 'revenue' | 'orders' | 'units' | 'margin' = 'revenue';
  /** Members the viewer has "entered" (drill by going inside), newest last. */
  inside: { dim: Dim; value: string | number }[] = [];
  private history: { filter: Filter; inside: { dim: Dim; value: string | number }[] }[] = [];
  private listeners: Listener[] = [];

  constructor(public cube: Cube) {}

  subscribe(fn: Listener): void {
    this.listeners.push(fn);
  }
  emit(): void {
    for (const l of this.listeners) l();
  }
  private push(): void {
    this.history.push({ filter: { ...this.filter }, inside: [...this.inside] });
    if (this.history.length > 40) this.history.shift();
  }

  /** Selecting a member filters by it; selecting it again clears that filter. */
  toggle(dim: Dim, value: string | number): void {
    this.push();
    if (this.filter[dim] === value) delete this.filter[dim];
    else this.filter[dim] = value;
    if (dim === 'category' && this.filter.product !== undefined) {
      const p = this.cube.products.find((x) => x.product === this.filter.product);
      if (p && this.filter.category !== undefined && p.category !== this.filter.category) delete this.filter.product;
    }
    this.emit();
  }

  set(dim: Dim, value: string | number | undefined): void {
    this.push();
    if (value === undefined) delete this.filter[dim];
    else this.filter[dim] = value;
    this.emit();
  }

  /** Drill by going inside a member: it becomes a filter and the room changes around the viewer. */
  enter(dim: Dim, value: string | number): void {
    this.push();
    this.filter[dim] = value;
    this.inside = this.inside.filter((i) => i.dim !== dim).concat({ dim, value });
    this.emit();
  }

  /** One step back (B / Y). Returns false when there is nothing to undo. */
  back(): boolean {
    const h = this.history.pop();
    if (!h) return false;
    this.filter = h.filter;
    this.inside = h.inside;
    this.emit();
    return true;
  }

  reset(): void {
    if (!Object.keys(this.filter).length && !this.inside.length) return;
    this.push();
    this.filter = {};
    this.inside = [];
    this.emit();
  }

  setMeasure(m: Store['measure']): void {
    this.measure = m;
    this.emit();
  }

  replaceCube(cube: Cube): void {
    this.cube = cube;
    this.emit();
  }
}
