"use client";

import React from "react";

interface FinneasMessageContentProps {
  content: string;
}

export const FinneasMessageContent: React.FC<FinneasMessageContentProps> = ({ content }) => {
  // Pre-clean line text:
  // 1. Strip all unicode emojis and pictographs
  // 2. Replace em dashes ("—") and en dashes ("–") with clean standard hyphen " - "
  // 3. Remove single emphasis asterisks (*word* -> word) while preserving **bold**
  // 4. Clean messy floats like ₹41,883.67 to clean ₹41,884
  const renderFormattedLine = (lineText: string) => {
    let clean = lineText || "";

    // 1. Strip ALL emojis
    clean = clean.replace(
      /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2702}-\u{27B0}\u{24C2}-\u{1F251}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}]/gu,
      ""
    );

    // 2. Replace em dashes / en dashes
    clean = clean.replace(/[—–]/g, " - ");

    // 3. Convert *word* to word (single asterisks) while preserving **bold**
    clean = clean.replace(/(?<!\*)\*([^\*\n]+?)\*(?!\*)/g, "$1");
    clean = clean.replace(/(?<!\*)\*(?!\*|\s)/g, "");

    // 4. Clean awkward float cents in rupee amounts: e.g. ₹41,883.67 -> ₹41,884
    clean = clean.replace(/₹\s*(\d{1,3}(?:,\d{2,3})*)\.\d+/g, (match, p1) => `₹${p1}`);

    // Split by **bold** tags first
    const parts = clean.split(/(\*\*.*?\*\*)/g);

    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={index} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }

      // For non-bold text: highlight financial figures and percentages uniformly
      // so all numbers have consistent font-semibold weight and color
      const subParts = part.split(/(₹\s*\d{1,3}(?:,\d{2,3})*(?:\s*(?:Lakhs?|Crores?|Cr|L|k))?|\b\d+(?:\.\d+)?%)/g);

      return (
        <span key={index}>
          {subParts.map((sub, sIdx) => {
            if (/^(₹|\d+(?:\.\d+)?%)/.test(sub.trim())) {
              return (
                <span key={sIdx} className="font-semibold text-slate-900">
                  {sub}
                </span>
              );
            }
            return <span key={sIdx}>{sub}</span>;
          })}
        </span>
      );
    });
  };

  const lines = (content || "").split("\n");
  const renderedElements: React.ReactNode[] = [];
  let currentList: string[] = [];
  let currentTable: string[] = [];

  const flushList = () => {
    if (currentList.length > 0) {
      renderedElements.push(
        <ul key={`list-${renderedElements.length}`} className="my-2 space-y-1.5 pl-4 list-disc list-outside text-slate-700 text-xs">
          {currentList.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderFormattedLine(item)}
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  const flushTable = () => {
    if (currentTable.length >= 2) {
      // First line is header, second is separator (|---|)
      const parseRow = (line: string) =>
        line
          .replace(/^\||\|$/g, "")
          .split("|")
          .map((c) => c.trim());

      const headerCells = parseRow(currentTable[0]);
      const bodyLines = currentTable.slice(1).filter((l) => !/^\|?\s*[-:]+[-| :]*\|?$/.test(l));
      const bodyRows = bodyLines.map(parseRow);

      renderedElements.push(
        <div
          key={`table-${renderedElements.length}`}
          className="my-3 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-2xs"
        >
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                {headerCells.map((h, i) => (
                  <th
                    key={i}
                    className="px-3 py-2 text-[11px] font-bold text-slate-900 border-r last:border-r-0 border-slate-200/80 whitespace-nowrap"
                  >
                    {renderFormattedLine(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {bodyRows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-slate-50/70 transition">
                  {row.map((cell, cIdx) => (
                    <td
                      key={cIdx}
                      className="px-3 py-2 text-[11px] border-r last:border-r-0 border-slate-200/80 leading-relaxed"
                    >
                      {renderFormattedLine(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      currentTable = [];
    } else if (currentTable.length > 0) {
      currentTable.forEach((l, idx) => {
        renderedElements.push(
          <p key={`tfallback-${idx}`} className="text-xs text-slate-700 leading-relaxed my-1">
            {renderFormattedLine(l)}
          </p>
        );
      });
      currentTable = [];
    }
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    // Table rows
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      flushList();
      currentTable.push(trimmed);
      return;
    } else {
      flushTable();
    }

    if (!trimmed) {
      flushList();
      renderedElements.push(<div key={`spacer-${index}`} className="h-2" />);
      return;
    }

    // Headings
    if (trimmed.startsWith("### ")) {
      flushList();
      renderedElements.push(
        <h4 key={`h3-${index}`} className="font-bold text-slate-900 text-sm mt-3 mb-1">
          {renderFormattedLine(trimmed.slice(4))}
        </h4>
      );
      return;
    }

    if (trimmed.startsWith("## ")) {
      flushList();
      renderedElements.push(
        <h3 key={`h2-${index}`} className="font-bold text-slate-900 text-base mt-3 mb-1.5">
          {renderFormattedLine(trimmed.slice(3))}
        </h3>
      );
      return;
    }

    // Bullet items
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ") || trimmed.startsWith("• ")) {
      currentList.push(trimmed.slice(2));
      return;
    }

    // Numbered lists (e.g. "1. ")
    const numMatch = trimmed.match(/^(\d+\.)\s+(.+)$/);
    if (numMatch) {
      flushList();
      renderedElements.push(
        <div key={`num-${index}`} className="flex items-start space-x-2 my-1 text-xs text-slate-700 leading-relaxed">
          <span className="font-bold text-slate-900 shrink-0">{numMatch[1]}</span>
          <div className="flex-1">{renderFormattedLine(numMatch[2])}</div>
        </div>
      );
      return;
    }

    // Regular paragraphs
    flushList();
    renderedElements.push(
      <p key={`p-${index}`} className="text-xs text-slate-700 leading-relaxed my-1">
        {renderFormattedLine(trimmed)}
      </p>
    );
  });

  flushList();
  flushTable();

  return <div className="space-y-0.5 text-xs text-slate-800 leading-relaxed">{renderedElements}</div>;
};
