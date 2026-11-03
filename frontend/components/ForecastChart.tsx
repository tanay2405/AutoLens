"use client";

import {
  Area, CartesianGrid, ComposedChart, Legend, Line,
  ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { TOOLTIP_STYLE, type ChartRow } from "@/lib/chart";

const b = (v: number) => `${v < 0 ? "-" : ""}$${Math.abs(v).toFixed(1)}B`;
const tick = { fill: "var(--muted)" };

export default function ForecastChart({ data }: { data: ChartRow[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--rule)" />
        <XAxis dataKey="year" tick={tick} stroke="var(--rule)" />
        <YAxis tickFormatter={(v: number) => `${v}B`} width={56} tick={tick} stroke="var(--rule)" />
        <ReferenceLine y={0} stroke="var(--muted)" />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          labelStyle={{ color: "var(--ink)" }}
          formatter={(value: unknown, name: unknown) => [
            Array.isArray(value) ? `${b(Number(value[0]))} to ${b(Number(value[1]))}` : b(Number(value)),
            String(name),
          ]}
        />
        <Legend wrapperStyle={{ color: "var(--muted)" }} />
        <Area dataKey="band" name="80% interval" stroke="none" fill="var(--forecast)"
              fillOpacity={0.2} isAnimationActive={false} />
        <Line dataKey="reported" name="Reported" stroke="var(--reported)" strokeWidth={2.5}
              dot={{ r: 3, fill: "var(--panel)" }} isAnimationActive={false} />
        <Line dataKey="forecast" name="Forecast" stroke="var(--forecast)" strokeWidth={2.5}
              strokeDasharray="6 4" dot={{ r: 3, fill: "var(--panel)" }} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}