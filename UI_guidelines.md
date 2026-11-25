# FIN — UI Design System & Guidelines (`UI_guidelines.md`)

> **Design Philosophy**: Crisp, clean, editorial light mode. High-end modern consumer fintech (Linear / Mercury / Apple aesthetic). Clean off-white surfaces, crisp typography, and purposeful soft-pastel & vibrant accents. No muddy dark mode slop.

---

## 1. Surfaces & Light Canvas Palette

* **Page Background**: `#F8FAFC` (Slate 50 — clean, soft, non-straining off-white)
* **Card Surface**: `#FFFFFF` (Pure crisp white with subtle 1px border `#E2E8F0` and soft shadow `shadow-sm`)
* **Elevated / Hover Surface**: `#F1F5F9` (Slate 100)
* **Primary Text**: `#0F172A` (Slate 900 — deep, readable ink black)
* **Muted Subtext**: `#64748B` (Slate 500)

---

## 2. Aesthetic Light Palette & Semantic Color Tokens

* **Indigo / Royal Blue (Primary Brand)**: `#4F46E5` / `#3B82F6` (Badges: `#EEF2FF`, text: `#4338CA`)
* **Vibrant Mint / Emerald (Inflow & Positive Alpha)**: `#059669` (Surface: `#ECFDF5`, text: `#047857`)
* **Soft Coral / Rose (Vulnerabilities & Outflow)**: `#E11D48` (Surface: `#FFF1F2`, text: `#BE123C`)
* **Warm Amber (Warnings, Creep, Subscriptions)**: `#D97706` (Surface: `#FFFBEB`, text: `#B45309`)
* **Electric Purple (Investments)**: `#7C3AED` (Surface: `#F5F3FF`, text: `#6D28D9`)
* **Sky Blue (Cashflow & Liquidity)**: `#0284C7` (Surface: `#F0F9FF`, text: `#0369A1`)

---

## 3. Typography & Numerical Styling

* **Display & Headings**: `Plus Jakarta Sans` font.
* **Numbers & Monies**: `JetBrains Mono` font with tabular lining figures (`font-mono font-bold text-slate-900`).
* **Micro-labels**: Uppercase, tracked out (`text-[11px] font-bold tracking-wider text-slate-500 font-mono`).

---

## 4. Zero-State / Empty State Rules

* When no statement has been uploaded by the user:
  * Do **NOT** pre-load demo data automatically without user intent.
  * Show a clean, welcoming **Empty State Screen**:
    * Clean hero upload card with drag-and-drop.
    * A clear secondary action: *"Or click to test with Demo Salaried Profile"*.
  * Only render the analytics, charts, health score, and drilldown tabs once a statement is actively ingested.
