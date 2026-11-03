"use client";

export default function ThemeToggle() {
  function toggle() {
    const next = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {}
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle light and dark mode"
      className="rounded border border-header-fg/40 px-2.5 py-1 text-sm hover:bg-header-fg/10"
    >
      <span className="dark:hidden">Dark mode</span>
      <span className="hidden dark:inline">Light mode</span>
    </button>
  );
}