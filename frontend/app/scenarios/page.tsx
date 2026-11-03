"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Bar, BarChart, CartesianGrid, Legend, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import Badge from "@/components/Badge"; // same import line as your other pages
import { API, Company } from "@/lib/api";
import { money, pct } from "@/lib/format";
import { TOOLTIP_STYLE } from "@/lib/chart";

interface Outcome {
  revenue: number;
  operating_income: number;
  operating_margin: number;
  capex: number;
  income_after_capex: number;
}
interface ScenarioResponse { baseline: Outcome; result: Outcome; delta: Outcome }

const DEFAULTS = {
  volume_change: 0,
  material_cost_change: 0,
  capex_change: 0,
  price_passthrough: 0,
  variable_cost_share: 0.8,
  material_share: 0.5,
};
type Params = typeof DEFAULTS;

const PRESETS: { label: string; values: Partial<Params> }[] = [
  { label: "Reset", values: {} },
  { label: "Mild downturn", values: { volume_change: -0.05, material_cost_change: 0.05 } },
  { label: "Severe stress", values: { volume_change: -0.15, material_cost_change: 0.15, capex_change: 0.2 } },
];

const signed = (v: number) => `${v > 0 ? "+" : ""}${Math.round(v * 100)}%`;
const plain = (v: number) => `${Math.round(v * 100)}%`;
const delta$ = (v: number) => `${v > 0 ? "+" : ""}${money(v)}`;

function Slider(props: {
  label: string; value: number; min: number; max: number; step: number;
  display: (v: number) => string; onChange: (v: number) => void; hint?: string;
}) {
  return (
    <label className="block">
      <div className="flex justify-between text-sm">
        <span>{props.label}</span>
        <span className="font-medium tabular-nums">{props.display(props.value)}</span>
      </div>
      <input type="range" className="mt-1 w-full accent-ink" min={props.min} max={props.max} step={props.step}
             value={props.value} onChange={(e) => props.onChange(Number(e.target.value))} />
      {props.hint && <p className="text-xs text-muted">{props.hint}</p>}
    </label>
  );
}

export default function ScenarioLab() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [ticker, setTicker] = useState("");
  const [year, setYear] = useState(2027);
  const [p, setP] = useState<Params>(DEFAULTS);
  const [data, setData] = useState<ScenarioResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/api/companies`)
      .then((r) => r.json())
      .then((cs: Company[]) => { setCompanies(cs); setTicker(cs[0]?.ticker ?? ""); })
      .catch(() => setError("Could not reach the API. Is uvicorn running?"));
  }, []);

  useEffect(() => {
    if (!ticker) return;
    const ctrl = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/api/scenarios`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ticker, year, ...p }),
          signal: ctrl.signal,
        });
        if (!res.ok) throw new Error(`API returned ${res.status}: ${await res.text()}`);
        setData(await res.json());
        setError(null);
      } catch (e) {
        if ((e as Error).name !== "AbortError") setError((e as Error).message);
      }
    }, 250); // debounce while dragging
    return () => { clearTimeout(timer); ctrl.abort(); };
  }, [ticker, year, p]);

  const set = <K extends keyof Params>(k: K) => (v: number) => setP((prev) => ({ ...prev, [k]: v }));
  const setVariableShare = (v: number) =>
    setP((prev) => ({ ...prev, variable_cost_share: v, material_share: Math.min(prev.material_share, v) }));

  const chartData = data && [
    { name: "Operating income", baseline: data.baseline.operating_income / 1e9, scenario: data.result.operating_income / 1e9 },
    { name: "Income after capex", baseline: data.baseline.income_after_capex / 1e9, scenario: data.result.income_after_capex / 1e9 },
  ];

  let headline = "";
  if (data) {
    const b = data.baseline.operating_income, r = data.result.operating_income;
    if (b > 0 && r < 0) headline = `Operating income turns negative: ${money(b)} → ${money(r)}.`;
    else if (b > 0) headline = `Operating income changes by ${((r - b) / b * 100).toFixed(0)}% versus baseline.`;
  }

  const rows: { label: string; key: keyof Outcome; fmt: (v: number) => string }[] = [
    { label: "Revenue", key: "revenue", fmt: money },
    { label: "Operating income", key: "operating_income", fmt: money },
    { label: "Operating margin", key: "operating_margin", fmt: (v) => pct(v) },
    { label: "Capex (derived)", key: "capex", fmt: money },
    { label: "Income after capex", key: "income_after_capex", fmt: money },
  ];

  return (
    <main className="mx-auto max-w-6xl p-6 md:p-10">
      <Link href="/" className="text-sm text-muted hover:underline">← Overview</Link>
      <h1 className="mt-2 text-3xl font-bold">Scenario lab</h1>
      <p className="mt-1 text-muted">
        Stress the baseline forecast and see how sensitive profit is. <Badge type="scenario" />
      </p>
      <p className="mt-2 note p-3 text-sm">
        Results come from baseline forecasts plus <strong>illustrative cost-structure assumptions</strong>, not
        reported figures. Treat the shape of the response, not the exact dollars, as the finding.
      </p>

      <div className="mt-6 grid gap-8 md:grid-cols-[320px_1fr]">
        <aside className="space-y-5">
          <div className="flex gap-2">
            <select className="w-full field"
                    value={ticker} onChange={(e) => setTicker(e.target.value)}>
              {companies.map((c) => <option key={c.ticker} value={c.ticker}>{c.name}</option>)}
            </select>
            <select className="field"
                    value={year} onChange={(e) => setYear(Number(e.target.value))}>
              {[2026, 2027, 2028].map((y) => <option key={y} value={y}>FY{y}</option>)}
            </select>
          </div>

          <div className="flex flex-wrap gap-2">
            {PRESETS.map((pre) => (
              <button key={pre.label} onClick={() => setP({ ...DEFAULTS, ...pre.values })}
                      className="field px-2 py-1 text-xs hover:bg-paper">
                {pre.label}
              </button>
            ))}
          </div>

          <h2 className="text-sm font-semibold text-ink">Shocks</h2>
          <Slider label="Production volume" value={p.volume_change} min={-0.3} max={0.1} step={0.01}
                  display={signed} onChange={set("volume_change")} />
          <Slider label="Material costs" value={p.material_cost_change} min={-0.1} max={0.3} step={0.01}
                  display={signed} onChange={set("material_cost_change")} />
          <Slider label="Capital spending" value={p.capex_change} min={-0.2} max={0.5} step={0.01}
                  display={signed} onChange={set("capex_change")} />

          <h2 className="text-sm font-semibold text-ink">Assumptions (illustrative)</h2>
          <Slider label="Variable share of costs" value={p.variable_cost_share} min={0.5} max={0.95} step={0.01}
                  display={plain} onChange={setVariableShare} hint="Higher = costs flex more with volume (less operating leverage)." />
          <Slider label="Material share of costs" value={p.material_share} min={0.1} max={p.variable_cost_share} step={0.01}
                  display={plain} onChange={set("material_share")} hint="Cannot exceed the variable share." />
          <Slider label="Price pass-through" value={p.price_passthrough} min={0} max={1} step={0.05}
                  display={plain} onChange={set("price_passthrough")} hint="Share of a material cost increase recovered through price." />
        </aside>

        <section>
          {error && <p className="note-error p-3 text-sm">{error}</p>}
          {data && chartData && (
            <>
              {headline && <p className="text-lg font-semibold">{headline}</p>}
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-right text-muted">
                      <th className="py-2 text-left">FY{year}</th>
                      <th>Baseline <Badge type="forecast" /></th>
                      <th>Scenario <Badge type="scenario" /></th>
                      <th>Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <tr key={r.key} className="border-t border-rule-soft text-right tabular-nums">
                        <td className="py-2 text-left font-medium">{r.label}</td>
                        <td>{r.fmt(data.baseline[r.key])}</td>
                        <td>{r.fmt(data.result[r.key])}</td>
                        <td className={data.delta[r.key] < 0 ? "text-neg" : data.delta[r.key] > 0 ? "text-pos" : ""}>
                          {r.key === "operating_margin"
                            ? `${data.delta[r.key] > 0 ? "+" : ""}${(data.delta[r.key] * 100).toFixed(1)} pts`
                            : delta$(data.delta[r.key])}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-6">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={chartData} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
                    <XAxis dataKey="name" tick={{ fill: "var(--muted)" }} stroke="var(--rule)" />
                    <YAxis tickFormatter={(v: number) => `${v}B`} width={56} tick={{ fill: "var(--muted)" }} stroke="var(--rule)" />
                    <ReferenceLine y={0} stroke="var(--muted)" />
                    <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={{ color: "var(--ink)" }} formatter={(v: unknown) => `${Number(v) < 0 ? "-" : ""}$${Math.abs(Number(v)).toFixed(1)}B`} />
                    <Legend wrapperStyle={{ color: "var(--muted)" }} />
                    <Bar dataKey="baseline" name="Baseline" fill="var(--baseline)" isAnimationActive={false} />
                    <Bar dataKey="scenario" name="Scenario" fill="var(--scenario)" isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}