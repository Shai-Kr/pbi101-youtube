// Aurora Sales, loaded once as a small cube (year x month x region x category x product).
// Every answer in the VR room is computed from this cube in memory, so interactions are instant.

export interface Row {
  year: number;
  month: number;
  region: string;
  category: string;
  product: string;
  revenue: number;
  cost: number;
  orders: number;
  units: number;
}

export type Dim = 'year' | 'month' | 'region' | 'category' | 'product';
export type Filter = Partial<Record<Dim, string | number>>;
export interface Totals {
  revenue: number;
  cost: number;
  orders: number;
  units: number;
}
export type MeasureKey = 'revenue' | 'orders' | 'units' | 'margin' | 'marginPct' | 'aov';

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function fmtMoney(v: number): string {
  const a = Math.abs(v);
  if (a >= 1e6) return `$${(v / 1e6).toFixed(a >= 1e7 ? 1 : 2)}M`;
  if (a >= 1e3) return `$${(v / 1e3).toFixed(a >= 1e5 ? 0 : 1)}K`;
  return `$${v.toFixed(0)}`;
}
export function fmtNum(v: number): string {
  return Math.round(v).toLocaleString('en-US');
}
export function fmtPct(v: number, signed = false): string {
  if (!isFinite(v)) return 'n/a';
  const s = (v * 100).toFixed(1) + '%';
  return signed && v > 0 ? '+' + s : s;
}

export const MEASURES: Record<MeasureKey, { label: string; fmt: (v: number) => string; of: (t: Totals) => number }> = {
  revenue: { label: 'Revenue', fmt: fmtMoney, of: (t) => t.revenue },
  orders: { label: 'Orders', fmt: fmtNum, of: (t) => t.orders },
  units: { label: 'Units', fmt: fmtNum, of: (t) => t.units },
  margin: { label: 'Gross margin', fmt: fmtMoney, of: (t) => t.revenue - t.cost },
  marginPct: { label: 'Margin %', fmt: (v) => fmtPct(v), of: (t) => (t.revenue ? (t.revenue - t.cost) / t.revenue : NaN) },
  aov: { label: 'Avg order', fmt: fmtMoney, of: (t) => (t.orders ? t.revenue / t.orders : NaN) },
};

export const DIM_LABEL: Record<Dim, string> = {
  year: 'Year',
  month: 'Month',
  region: 'Region',
  category: 'Category',
  product: 'Product',
};

export function memberLabel(dim: Dim, v: string | number): string {
  return dim === 'month' ? MONTHS[Number(v) - 1] : String(v);
}

export function filterText(f: Filter): string {
  const parts: string[] = [];
  for (const d of ['year', 'month', 'region', 'category', 'product'] as Dim[]) {
    if (f[d] !== undefined) parts.push(memberLabel(d, f[d]!));
  }
  return parts.length ? parts.join(' · ') : 'Everything';
}

const zero = (): Totals => ({ revenue: 0, cost: 0, orders: 0, units: 0 });

export class Cube {
  readonly years: number[];
  readonly regions: string[];
  readonly categories: string[];
  readonly products: { product: string; category: string }[];
  /** The newest year and the months it has data for (the year is not complete). */
  readonly latestYear: number;
  readonly latestMonths: number[];

  constructor(readonly rows: Row[]) {
    this.years = [...new Set(rows.map((r) => r.year))].sort();
    this.latestYear = this.years[this.years.length - 1];
    this.latestMonths = [...new Set(rows.filter((r) => r.year === this.latestYear).map((r) => r.month))].sort((a, b) => a - b);
    this.regions = this.order('region');
    this.categories = this.order('category');
    const cat = new Map<string, string>();
    rows.forEach((r) => cat.set(r.product, r.category));
    this.products = this.order('product').map((p) => ({ product: p, category: cat.get(p)! }));
  }

  private order(dim: 'region' | 'category' | 'product'): string[] {
    const m = new Map<string, number>();
    for (const r of this.rows) m.set(r[dim], (m.get(r[dim]) ?? 0) + r.revenue);
    return [...m.entries()].sort((a, b) => b[1] - a[1]).map((e) => e[0]);
  }

  private match(r: Row, f: Filter): boolean {
    return (
      (f.year === undefined || r.year === f.year) &&
      (f.month === undefined || r.month === f.month) &&
      (f.region === undefined || r.region === f.region) &&
      (f.category === undefined || r.category === f.category) &&
      (f.product === undefined || r.product === f.product)
    );
  }

  totals(f: Filter = {}): Totals {
    const t = zero();
    for (const r of this.rows) {
      if (!this.match(r, f)) continue;
      t.revenue += r.revenue;
      t.cost += r.cost;
      t.orders += r.orders;
      t.units += r.units;
    }
    return t;
  }

  measure(key: MeasureKey, f: Filter = {}): number {
    return MEASURES[key].of(this.totals(f));
  }

  members(dim: Dim, f: Filter = {}): (string | number)[] {
    if (dim === 'year') return this.years;
    if (dim === 'month') return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    if (dim === 'region') return this.regions;
    if (dim === 'category') return this.categories;
    return this.products.filter((p) => f.category === undefined || p.category === f.category).map((p) => p.product);
  }

  /** Totals per member of a dimension, inside the filter (the filter on that same dimension is ignored). */
  by(dim: Dim, f: Filter = {}): { key: string | number; totals: Totals }[] {
    const g: Filter = { ...f };
    delete g[dim];
    const m = new Map<string | number, Totals>();
    for (const k of this.members(dim, g)) m.set(k, zero());
    for (const r of this.rows) {
      if (!this.match(r, g)) continue;
      const t = m.get(r[dim]);
      if (!t) continue;
      t.revenue += r.revenue;
      t.cost += r.cost;
      t.orders += r.orders;
      t.units += r.units;
    }
    return [...m.entries()].map(([key, totals]) => ({ key, totals }));
  }

  /** Newest year against the same months of the year before (the filter's own year is ignored). */
  yoy(f: Filter = {}, key: MeasureKey = 'revenue'): { cur: number; prev: number; pct: number } {
    const g: Filter = { ...f };
    delete g.year;
    const months = g.month !== undefined ? [Number(g.month)] : this.latestMonths;
    delete g.month;
    const cur = zero();
    const prev = zero();
    for (const r of this.rows) {
      if (!this.match(r, g) || !months.includes(r.month)) continue;
      const t = r.year === this.latestYear ? cur : r.year === this.latestYear - 1 ? prev : null;
      if (!t) continue;
      t.revenue += r.revenue;
      t.cost += r.cost;
      t.orders += r.orders;
      t.units += r.units;
    }
    const c = MEASURES[key].of(cur);
    const p = MEASURES[key].of(prev);
    return { cur: c, prev: p, pct: p ? (c - p) / p : NaN };
  }
}

/** Builds the cube from a query result: column names as the semantic model returns them, rows as arrays. */
export function cubeFromTable(columns: string[], rows: unknown[][]): Cube {
  const idx = (needle: string) => {
    const i = columns.findIndex((c) => c.replace(/'/g, '').toLowerCase().includes(needle.toLowerCase()));
    if (i < 0) throw new Error(`Aurora query: column "${needle}" is missing (got ${columns.join(', ')})`);
    return i;
  };
  const c = {
    year: idx('[Year]'),
    month: idx('[Month Number]'),
    region: idx('[Region]'),
    category: idx('[Category]'),
    product: idx('[Product]'),
    revenue: idx('[Revenue]'),
    cost: idx('[Cost]'),
    orders: idx('[Orders]'),
    units: idx('[Units]'),
  };
  return new Cube(
    rows.map((r) => ({
      year: Number(r[c.year]),
      month: Number(r[c.month]),
      region: String(r[c.region]),
      category: String(r[c.category]),
      product: String(r[c.product]),
      revenue: Number(r[c.revenue] ?? 0),
      cost: Number(r[c.cost] ?? 0),
      orders: Number(r[c.orders] ?? 0),
      units: Number(r[c.units] ?? 0),
    }))
  );
}

export const REGION_COLORS: Record<string, number> = {
  'North America': 0x2f7dff,
  Europe: 0x00e0c0,
  'Asia Pacific': 0xffb020,
  'Latin America': 0xff3d9e,
};
export const CATEGORY_COLORS: Record<string, number> = {
  Camping: 0x7a5cff,
  Hiking: 0x27e0a0,
  Apparel: 0xff5a6e,
  Accessories: 0xffd23a,
};
const FALLBACK = [0x4aa8ff, 0x3ee08f, 0xff9a3c, 0xb47bff, 0xff6fb5, 0x35d8f0];
export function colorOf(dim: Dim, key: string | number, i = 0): number {
  if (dim === 'region') return REGION_COLORS[String(key)] ?? FALLBACK[i % FALLBACK.length];
  if (dim === 'category') return CATEGORY_COLORS[String(key)] ?? FALLBACK[i % FALLBACK.length];
  return FALLBACK[i % FALLBACK.length];
}
