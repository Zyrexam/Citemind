import "./globals.css";
import type { Metadata } from "next";
import { Source_Serif_4, Libre_Franklin } from "next/font/google";

const text = Source_Serif_4({
  subsets: ["latin"],
  weight: ["400", "600"],
  style: ["normal", "italic"],
  variable: "--font-text",
  display: "swap",
});

const ui = Libre_Franklin({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-ui",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CiteMind",
  description: "Research that shows its sources",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${text.variable} ${ui.variable}`}>
      <body className="min-h-screen">
        <header className="border-b border-rule">
          <div className="mx-auto max-w-6xl px-6 sm:px-8">
            <div className="flex h-14 items-center">
              <span className="font-text text-[1.0625rem] font-semibold tracking-[-0.01em] text-ink">
                CiteMind
              </span>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 pb-24 pt-10 sm:px-8">{children}</main>
      </body>
    </html>
  );
}
