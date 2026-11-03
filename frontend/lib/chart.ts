import { Observation } from "@/lib/api";

export interface ChartRow {
  year: number;
  reported?: number;
  forecast?: number;
  band?: [number, number];
}

/** Observations (USD) -> one row per year, in $B, with the forecast line joined to the last actual. */
export function buildSeries(obs: Observation[]): ChartRow[] {
  const byYear = new Map<number, ChartRow>();
  for (const o of obs) {
    if (o.period_type !== "annual") continue;
    const year = Number(o.period_end.slice(0, 4));
    const row = byYear.get(year) ?? { year };
    if (o.data_type === "reported") row.reported = o.value / 1e9;
    if (o.data_type === "forecast" && o.lower_bound != null && o.upper_bound != null) {
      row.forecast = o.value / 1e9;
      row.band = [o.lower_bound / 1e9, o.upper_bound / 1e9];
    }
    byYear.set(year, row);
  }
  const rows = [...byYear.values()].sort((a, b) => a.year - b.year);

  // Start the dashed line at the last actual value so the two lines connect.
  const last = [...rows].reverse().find((r) => r.reported != null);
  if (last && rows.some((r) => r.forecast != null)) {
    last.forecast = last.reported;
    last.band = [last.reported!, last.reported!];
  }
  return rows;
}

export const TOOLTIP_STYLE = {
  background: "var(--panel)",
  border: "1px solid var(--rule)",
  borderRadius: 4,
  color: "var(--ink)",
};