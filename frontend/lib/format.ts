export const money = (v: number | null) =>
  v == null ? "—" : `${v < 0 ? "-" : ""}$${(Math.abs(v) / 1e9).toFixed(1)}B`;

export const pct = (v: number | null, digits = 1) =>
  v == null ? "—" : `${(v * 100).toFixed(digits)}%`;

export const signedPct = (v: number | null) =>
  v == null ? "—" : `${v >= 0 ? "+" : ""}${(v * 100).toFixed(1)}%`;