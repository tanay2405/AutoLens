import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { Archivo } from "next/font/google";
import ThemeToggle from "@/components/ThemeToggle";
import "./globals.css";

const archivo = Archivo({ subsets: ["latin"], axes: ["wdth"], variable: "--font-archivo" });

export const metadata: Metadata = {
  title: "AutoLens",
  description: "Financial and manufacturing intelligence for automakers",
};

function BandMark() {
  return (
    <svg width="44" height="24" viewBox="0 0 44 24" aria-hidden="true">
      <polygon points="18,14 42,4 42,20" fill="#F2A65A" fillOpacity="0.35" />
      <polyline points="2,20 8,17 13,18 18,14" fill="none" stroke="#EBEFF3" strokeWidth="2.5"
                strokeLinejoin="round" strokeLinecap="round" />
      <line x1="18" y1="14" x2="42" y2="12" stroke="#F2A65A" strokeWidth="2.5" strokeDasharray="4 3" />
    </svg>
  );
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={archivo.variable}>
      <body className="min-h-screen antialiased">
        <header className="bg-header text-header-fg">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3 md:px-10">
            <Link href="/" className="flex items-center gap-3">
              <BandMark />
              <span className="text-2xl font-bold" style={{ fontVariationSettings: '"wdth" 70' }}>
                AutoLens
              </span>
            </Link>
            <nav className="flex items-center gap-6 text-sm">
              <Link href="/" className="hover:underline">Overview</Link>
              <Link href="/scenarios" className="hover:underline">Scenario lab</Link>
              <Link href="/sources" className="hover:underline">Data sources</Link>
              <ThemeToggle />
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}