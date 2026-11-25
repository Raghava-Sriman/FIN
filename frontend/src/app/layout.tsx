import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "FinSight",
  description: "Personal finance and cashflow intelligence engine.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body
        className="antialiased bg-[#F9FAFB] text-[#111827] font-sans selection:bg-slate-200"
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}
