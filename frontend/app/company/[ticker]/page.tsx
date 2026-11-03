import { Suspense } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import Badge from "@/components/Badge"; // use the same import line as in your app/page.tsx
import ForecastChart from "@/components/ForecastChart";
import { get, Company, Flag, Observation, SummaryRow } from "@/lib/api";
import { buildSeries } from "@/lib/chart";
import { money, pct, signedPct } from "@/lib/format";

function ChartCard({ title, obs }: { title: string; obs: Observation[] }) {
  const model = obs.find((o) => o.data_type === "forecast")?.model_name;
  return (
    <section className="panel mt-8 p-5">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-lg font-semibold">{title}</h2>
        <Badge type="reported" />
        <Badge type="forecast" />
      </div>
      <p className="mt-1 text-sm text-muted">
        Solid line: reported history. Dashed line and shaded band: baseline projection
        {model ? ` (model: ${model})` : ""} with an 80% interval. A trend-based projection, not a prediction.
      </p>
      <div className="mt-4">
        <ForecastChart data={buildSeries(obs)} />
      </div>
    </section>
  );
}

async function CompanyContent({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker: raw } = await params;
  const ticker = raw.toUpperCase();

  const companies = await get<Company[]>("/api/companies");
  const company = companies.find((c) => c.ticker === ticker);
  if (!company) notFound();

  const [summary, revenue, opIncome, flags] = await Promise.all([
    get<{ rows: SummaryRow[] }>(`/api/companies/${ticker}/summary`),
    get<Observation[]>(`/api/companies/${ticker}/observations?metric=revenue`),
    get<Observation[]>(`/api/companies/${ticker}/observations?metric=operating_income`),
    get<Flag[]>(`/api/anomalies?ticker=${ticker}`),
  ]);

  const rows = summary.rows.filter((r) => r.revenue != null && r.year >= 2019).reverse();

  return (
    <main className="mx-auto max-w-6xl p-6 md:p-10">
      <Link href="/" className="text-sm text-muted hover:underline">← All companies</Link>
      <h1 className="mt-2 text-3xl font-bold">{company.name}</h1>

      <ChartCard title="Revenue" obs={revenue} />
      <ChartCard title="Operating income" obs={opIncome} />

      <section className="panel mt-8 p-5">
        <h2 className="text-lg font-semibold">Annual metrics</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-right text-muted">
                <th className="py-2 text-left">Year</th>
                <th>Revenue <Badge type="reported" /></th>
                <th>Op. income <Badge type="reported" /></th>
                <th>Op. margin <Badge type="derived" /></th>
                <th>Revenue growth <Badge type="derived" /></th>
                <th>Volume growth <Badge type="derived" /></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.year} className="border-t border-rule-soft text-right tabular-nums">
                  <td className="py-2 text-left font-medium">{r.year}</td>
                  <td>{money(r.revenue)}</td>
                  <td>{money(r.operating_income)}</td>
                  <td className={r.operating_margin != null && r.operating_margin < 0 ? "text-neg" : ""}>
                    {pct(r.operating_margin)}
                  </td>
                  <td>{signedPct(r.revenue_yoy)}</td>
                  <td>{signedPct(r.volume_yoy)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold">Signals worth investigating</h2>
        <ul className="mt-3 space-y-2">
          {flags.map((f, i) => (
            <li key={i} className="panel p-3 text-sm">
              <span className="font-semibold">{f.year}</span>
              <span className={`ml-2 text-sm font-semibold capitalize ${
                f.severity === "high" ? "text-neg" : f.severity === "medium" ? "text-forecast" : "text-muted/60"}`}>
                {f.severity}
              </span>
              <p className="mt-1 text-muted">{f.message}</p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

export default function CompanyPage({ params }: { params: Promise<{ ticker: string }> }) {
  return (
    <Suspense fallback={<p className="p-10 text-muted">Loading company data…</p>}>
      <CompanyContent params={params} />
    </Suspense>
  );
}