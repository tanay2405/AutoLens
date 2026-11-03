const STYLE: Record<string, { text: string; mark: string; hint: string }> = {
  reported: { text: "text-reported", mark: "rounded-[1px] bg-reported", hint: "Published in a filing or release" },
  derived: { text: "text-derived", mark: "rounded-full bg-derived", hint: "Calculated by AutoLens from reported figures" },
  forecast: { text: "text-forecast", mark: "rounded-full border-[1.5px] border-dashed border-forecast", hint: "Model projection, not a prediction" },
  scenario: { text: "text-scenario", mark: "rotate-45 bg-scenario", hint: "Result of a what-if scenario" },
  estimated: { text: "text-muted", mark: "rounded-full border-[1.5px] border-muted", hint: "Estimated figure" },
};

export default function Badge({ type }: { type: string }) {
  const s = STYLE[type] ?? STYLE.estimated;
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${s.text}`} title={s.hint}>
      <span aria-hidden="true" className={`inline-block h-2 w-2 ${s.mark}`} />
      {type}
    </span>
  );
}