export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export interface Company { ticker: string; name: string }

export interface SummaryRow {
  year: number;
  revenue: number | null;
  operating_income: number | null;
  net_income: number | null;
  capex: number | null;
  total_costs: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  capex_pct_revenue: number | null;
  revenue_yoy: number | null;
  volume: number | null;
  volume_yoy: number | null;
  revenue_minus_volume_growth: number | null;
}

export interface Flag {
  ticker: string;
  year: number;
  rule: string;
  severity: "high" | "medium" | "low";
  message: string;
}

export async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return res.json();
}

export interface Observation {
  metric: string;
  unit: string;
  period_end: string;
  period_type: string;
  value: number;
  data_type: "reported" | "estimated" | "forecast";
  lower_bound: number | null;
  upper_bound: number | null;
  model_name: string | null;
  source: string;
  source_url: string | null;
}

export interface MetricDef {
  key: string;
  label: string;
  unit: string;
  category: string;
}