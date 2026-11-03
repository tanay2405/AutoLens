import { Suspense } from "react";
import Link from "next/link";
import Badge from "@/components/Badge";
import { get, Company, Flag, SummaryRow } from "@/lib/api";
import { money, pct, signedPct } from "@/lib/format";

const toneOf = (v: number | null) => (v == null ? "text-muted" : v < 0 ? "text-neg" : "text-pos");

const ROWS: { label: string; type: string; value: (r: SummaryRow) => string; tone?: (r: SummaryRow) => string }[] = [
  { label: "Revenue", type: "reported", value: (r) => money(r.revenue) },
  { label: "Revenue growth", type: "derived", value: (r) => signedPct(r.revenue_yoy), tone: (r) => toneOf(r.revenue_yoy) },
  { label: "Operating income", type: "reported", value: (r) => money(r.operating_income),
    tone: (r) => (r.operating_income != null && r.operating_income < 0 ? "text-neg" : "") },
  { label: "Operating margin", type: "derived", value: (r) => pct(r.operating_margin), tone: (r) => toneOf(r.operating_margin) },
  { label: "Volume growth", type: "derived", value: (r) => signedPct(r.volume_yoy), tone: (r) => toneOf(r.volume_yoy) },
];

const RULE = { high: "border-l-neg", medium: "border-l-forecast", low: "border-l-rule" } as const;
const WORD = { high: "text-neg", medium: "text-forecast", low: "text-muted" } as const;

async function Overview() {
  const companies = await get<Company[]>("/api/companies");
  const [summaries, flags] = await Promise.all([
    Promise.all(companies.map((c) => get<{ rows: SummaryRow[] }>(`/api/companies/${c.ticker}/summary`))),
    get<Flag[]>("/api/anomalies"),
  ]);
  const latest = summaries.map((s) => {
    const rows = s.rows.filter((r) => r.revenue != null);
    return rows[rows.length - 1];
  });
  const signals = flags.filter((f) => f.severity !== "low").slice(0, 6);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10 md:px-10">
      <h1 className="text-4xl font-bold">Ford, GM, and Tesla side by side</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Reported figures from SEC filings, with derived metrics and forecasts labeled so you can
        always tell which is which.
      </p>

      <section className="panel mt-8 overflow-x-auto">
        <table className="w-full min-w-[560px]">
          <thead>
            <tr className="border-b border-rule">
              <th className="p-4 text-left text-sm font-normal text-muted">Latest fiscal year</th>
              {companies.map((c, i) => (
                <th key={c.ticker} className="p-4 text-right font-normal">
                  <h2 className="text-2xl font-bold">
                    <Link href={`/company/${c.ticker}`} className="hover:underline">{c.name}</Link>
                  </h2>
                  <span className="text-sm text-muted">FY{latest[i].year}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.label} className="border-t border-rule-soft">
                <th scope="row" className="p-4 text-left font-normal">
                  <span className="block">{row.label}</span>
                  <Badge type={row.type} />
                </th>
                {latest.map((r, i) => (
                  <td key={companies[i].ticker}
                      className={`p-4 text-right text-xl font-semibold tabular-nums ${row.tone?.(r) ?? ""}`}>
                    {row.value(r)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm text-muted">
        <li className="flex items-center gap-2"><Badge type="reported" /> published in a filing</li>
        <li className="flex items-center gap-2"><Badge type="derived" /> calculated from reported figures</li>
        <li className="flex items-center gap-2"><Badge type="forecast" /> model projection, shown on company pages</li>
      </ul>

      <section className="mt-12">
        <h2 className="text-2xl font-bold">Signals worth investigating</h2>
        <p className="mt-1 text-sm text-muted">
          Flagged automatically by transparent rules. A flag shows that something is unusual, not why.
        </p>
        <ul className="mt-4 space-y-3">
          {signals.map((f, i) => (
            <li key={i} className={`panel border-l-4 ${RULE[f.severity]} p-4`}>
              <span className="font-semibold">{f.ticker} {f.year}</span>
              <span className={`ml-2 text-sm font-semibold capitalize ${WORD[f.severity]}`}>{f.severity}</span>
              <p className="mt-1 text-sm text-muted">{f.message}</p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<p className="p-10 text-muted">Loading AutoLens…</p>}>
      <Overview />
    </Suspense>
  );
}