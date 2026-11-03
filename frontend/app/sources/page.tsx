import { Suspense } from "react";
import Link from "next/link";
import SourcesTable, { SourceRow } from "@/components/SourcesTable";
import { get, Company, MetricDef, Observation } from "@/lib/api";

const NOTES: { title: string; body: string }[] = [
  {
    title: "Financials come from SEC filings",
    body: "Annual revenue, costs, income, and capex are read from SEC EDGAR XBRL data for each company's 10-K. When a year appears in several filings, the most recently filed value is used, so figures reflect any later restatement. Each row links to the filing it came from.",
  },
  {
    title: "Revenue includes financing arms",
    body: "Ford and GM revenue includes their captive finance businesses (Ford Credit, GM Financial). Growth rates and margins are comparable across companies; absolute levels are not purely automotive.",
  },
  {
    title: "Cost of revenue is not comparable, so we derive total costs",
    body: "Ford's cost-of-sales line may not include its finance arm's expenses while its revenue does, so a gross margin built from it can overstate profitability. GM does not report a cost-of-sales line in SEC structured data, so it is left empty. Instead, AutoLens derives total costs as revenue minus operating income for all three companies, and labels it derived.",
  },
  {
    title: "Volume metrics measure different things",
    body: "Tesla reports deliveries and production. Ford and GM report wholesales (vehicles sold to dealers); Ford's figure includes affiliate-built units, and GM's excludes its China joint ventures. Ford and GM do not publish a global production total, so it is shown as not reported. Growth rates are compared across companies, not levels.",
  },
  {
    title: "Open data item: Tesla 2021 deliveries",
    body: "Sources disagree on Tesla's 2021 deliveries (936,172 versus 936,222), so the figure is excluded until checked against Tesla's primary documents.",
  },
  {
    title: "Some Tesla volume rows cite news coverage",
    body: "Tesla's volume rows link to articles reporting its quarterly releases, not Tesla's own pages. Every figure matched at least two independent sources, but primary links are planned.",
  },
  {
    title: "Forecasts are baseline projections, not predictions",
    body: "Each forecast uses the simple model with the lowest backtest error, with an 80% interval built from that model's past errors. They cannot anticipate one-time charges, product launches, tariffs, or recalls, and they do not yet use 2026 year-to-date results.",
  },
  {
    title: "Scenario results use illustrative assumptions",
    body: "The scenario lab combines baseline forecasts with adjustable cost-structure assumptions (variable-cost share, material share, price pass-through). These are not reported figures; the shape of the response matters more than exact dollars.",
  },
];

async function SourcesContent() {
  const [companies, metrics] = await Promise.all([
    get<Company[]>("/api/companies"),
    get<MetricDef[]>("/api/metrics"),
  ]);
  const perCompany = await Promise.all(
    companies.map((c) => get<Observation[]>(`/api/companies/${c.ticker}/observations`)),
  );
  const rows: SourceRow[] = perCompany.flatMap((obs, i) =>
    obs.map((o) => ({ ...o, ticker: companies[i].ticker })),
  );

  function coverage(ticker: string, metric: string): string | null {
    const years = Array.from(new Set(
      rows.filter((r) => r.ticker === ticker && r.metric === metric && r.data_type === "reported")
          .map((r) => Number(r.period_end.slice(0, 4))),
    )).sort();
    return years.length ? `${years[0]}–${years[years.length - 1]} (${years.length})` : null;
  }

  return (
    <main className="mx-auto max-w-6xl p-6 md:p-10">
      <Link href="/" className="text-sm text-muted hover:underline">← Overview</Link>
      <h1 className="mt-2 text-3xl font-bold">Data sources and quality</h1>
      <p className="mt-1 text-muted">
        Every number in AutoLens is labeled reported, derived, forecast, or scenario. This page shows
        where each stored value came from, what is missing, and what to keep in mind when comparing companies.
      </p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Coverage of reported data</h2>
        <p className="text-sm text-muted">Years available (count in parentheses). A dash means not available.</p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted">
                <th className="py-2">Metric</th>
                {companies.map((c) => <th key={c.ticker}>{c.ticker}</th>)}
              </tr>
            </thead>
            <tbody>
              {metrics.map((m) => (
                <tr key={m.key} className="border-t border-rule-soft">
                  <td className="py-2 font-medium">{m.label}</td>
                  {companies.map((c) => {
                    const cov = coverage(c.ticker, m.key);
                    return (
                      <td key={c.ticker} className={`tabular-nums ${cov ? "" : "text-muted/60"}`}>
                        {cov ?? "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-semibold">Definitions and known limitations</h2>
        <ul className="mt-3 space-y-3">
          {NOTES.map((n) => (
            <li key={n.title} className="panel p-4">
              <p className="font-semibold">{n.title}</p>
              <p className="mt-1 text-sm text-muted">{n.body}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-semibold">All data points</h2>
        <div className="mt-3">
          <SourcesTable rows={rows} />
        </div>
      </section>
    </main>
  );
}

export default function SourcesPage() {
  return (
    <Suspense fallback={<p className="p-10 text-muted">Loading sources…</p>}>
      <SourcesContent />
    </Suspense>
  );
}