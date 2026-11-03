"use client";

import { useMemo, useState } from "react";
import Badge from "@/components/Badge"; // same import line as your other files
import type { Observation } from "@/lib/api";
import { money } from "@/lib/format";

export type SourceRow = Observation & { ticker: string };

const num = (v: number) => Math.round(v).toLocaleString("en-US");
const fmt = (unit: string, v: number) => (unit === "USD" ? money(v) : num(v));

function Select(props: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <label className="text-sm">
      <span className="mr-2 text-muted">{props.label}</span>
      <select className="field"
              value={props.value} onChange={(e) => props.onChange(e.target.value)}>
        <option value="all">All</option>
        {props.options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}

export default function SourcesTable({ rows }: { rows: SourceRow[] }) {
  const [ticker, setTicker] = useState("all");
  const [metric, setMetric] = useState("all");
  const [type, setType] = useState("all");

  const tickers = useMemo(() => Array.from(new Set(rows.map((r) => r.ticker))).sort(), [rows]);
  const metrics = useMemo(() => Array.from(new Set(rows.map((r) => r.metric))).sort(), [rows]);
  const types = useMemo(() => Array.from(new Set(rows.map((r) => r.data_type))).sort(), [rows]);

  const shown = useMemo(
    () =>
      rows
        .filter((r) => (ticker === "all" || r.ticker === ticker)
          && (metric === "all" || r.metric === metric)
          && (type === "all" || r.data_type === type))
        .sort((a, b) =>
          a.ticker.localeCompare(b.ticker) || a.metric.localeCompare(b.metric) ||
          b.period_end.localeCompare(a.period_end)),
    [rows, ticker, metric, type],
  );

  return (
    <div>
      <div className="flex flex-wrap items-center gap-4">
        <Select label="Company" value={ticker} options={tickers} onChange={setTicker} />
        <Select label="Metric" value={metric} options={metrics} onChange={setMetric} />
        <Select label="Type" value={type} options={types} onChange={setType} />
        <span className="text-sm text-muted">{shown.length} of {rows.length} data points</span>
      </div>

      <div className="mt-4 panel max-h-[600px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-panel text-left text-muted">
            <tr>
              <th className="p-2">Company</th>
              <th>Metric</th>
              <th>Period end</th>
              <th className="text-right">Value</th>
              <th className="pl-4">Type</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r, i) => (
              <tr key={i} className="border-t border-rule-soft align-top">
                <td className="p-2 font-medium">{r.ticker}</td>
                <td>{r.metric}</td>
                <td className="tabular-nums">{r.period_end}</td>
                <td className="text-right tabular-nums">
                  {fmt(r.unit, r.value)}
                  {r.data_type === "forecast" && r.lower_bound != null && r.upper_bound != null && (
                    <div className="text-xs text-muted">
                      80%: {fmt(r.unit, r.lower_bound)} to {fmt(r.unit, r.upper_bound)}
                    </div>
                  )}
                </td>
                <td className="pl-4"><Badge type={r.data_type} /></td>
                <td className="max-w-md py-2 pr-2 text-muted">
                  {r.source}
                  {r.source_url && (
                    <a href={r.source_url} target="_blank" rel="noreferrer"
                       className="ml-2 whitespace-nowrap underline">open ↗</a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}