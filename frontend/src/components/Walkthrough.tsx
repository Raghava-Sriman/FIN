"use client";

import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { X } from "lucide-react";

export type WalkthroughStep = {
  /** Value of the data-tour attribute on the element to highlight */
  target: string;
  title: string;
  body: string;
  /** Called before the step is shown, e.g. to switch to the tab that contains the target */
  onEnter?: () => void;
};

type Rect = { top: number; left: number; width: number; height: number };

const PADDING = 8;
const CARD_WIDTH = 340;
const CARD_HEIGHT = 220; // approximate; used only to decide where the card fits
const TARGET_WAIT_MS = 2500;

export function Walkthrough({ steps, onClose }: { steps: WalkthroughStep[]; onClose: () => void }) {
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState<Rect | null>(null);
  const [viewport, setViewport] = useState({ width: 0, height: 0 });
  const cardRef = useRef<HTMLDivElement | null>(null);
  const step = steps[index];
  const isLast = index === steps.length - 1;

  const measure = useCallback(() => {
    setViewport({ width: window.innerWidth, height: window.innerHeight });
    const el = document.querySelector<HTMLElement>(`[data-tour="${step.target}"]`);
    if (!el) {
      setRect(null);
      return;
    }
    const r = el.getBoundingClientRect();
    setRect({ top: r.top - PADDING, left: r.left - PADDING, width: r.width + PADDING * 2, height: r.height + PADDING * 2 });
  }, [step.target]);

  // Enter the step (switch tab), then wait for the target to render and bring it into view
  useEffect(() => {
    step.onEnter?.();
    const started = Date.now();
    let frame = 0;
    const find = () => {
      const el = document.querySelector<HTMLElement>(`[data-tour="${step.target}"]`);
      if (el) {
        el.scrollIntoView({ block: "center", behavior: "auto" });
        frame = requestAnimationFrame(measure);
      } else if (Date.now() - started < TARGET_WAIT_MS) {
        frame = requestAnimationFrame(find);
      } else {
        measure();
      }
    };
    frame = requestAnimationFrame(find);
    return () => cancelAnimationFrame(frame);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  useLayoutEffect(() => {
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    return () => {
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
    };
  }, [measure]);

  // Clear the old spotlight while the next step's target is being located
  const goTo = useCallback((i: number) => {
    setRect(null);
    setIndex(i);
  }, []);
  const next = useCallback(() => (isLast ? onClose() : goTo(index + 1)), [isLast, onClose, goTo, index]);
  const back = useCallback(() => goTo(Math.max(0, index - 1)), [goTo, index]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") back();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, back, onClose]);

  useEffect(() => {
    cardRef.current?.focus();
  }, [index]);

  // Place the card below the target, else above, else beside it (tall targets), else in a corner.
  // Phones get a bottom sheet; a missing target gets a centered card.
  const isPhone = viewport.width > 0 && viewport.width < 640;
  let cardStyle: React.CSSProperties;
  if (isPhone) {
    cardStyle = { left: 16, right: 16, bottom: 16 };
  } else if (rect) {
    const left = Math.min(Math.max(16, rect.left), viewport.width - CARD_WIDTH - 16);
    const below = rect.top + rect.height + 12;
    const above = rect.top - CARD_HEIGHT - 12;
    const sideTop = Math.min(Math.max(16, rect.top), viewport.height - CARD_HEIGHT - 16);
    if (below + CARD_HEIGHT < viewport.height) {
      cardStyle = { top: below, left, width: CARD_WIDTH };
    } else if (above >= 16) {
      cardStyle = { top: above, left, width: CARD_WIDTH };
    } else if (rect.left + rect.width + CARD_WIDTH + 24 < viewport.width) {
      cardStyle = { top: sideTop, left: rect.left + rect.width + 12, width: CARD_WIDTH };
    } else if (rect.left - CARD_WIDTH - 24 > 0) {
      cardStyle = { top: sideTop, left: rect.left - CARD_WIDTH - 12, width: CARD_WIDTH };
    } else {
      cardStyle = { right: 16, bottom: 16, width: CARD_WIDTH };
    }
  } else {
    cardStyle = { top: "50%", left: "50%", width: CARD_WIDTH, transform: "translate(-50%, -50%)" };
  }

  return (
    <div className="fixed inset-0 z-[100]" aria-live="polite">
      {/* Dimmed backdrop with a spotlight cut out around the target */}
      {rect ? (
        <div
          className="fixed rounded-xl ring-2 ring-white/80 pointer-events-none transition-all duration-200"
          style={{ ...rect, boxShadow: "0 0 0 9999px rgba(15, 23, 42, 0.55)" }}
        />
      ) : (
        <div className="fixed inset-0 bg-slate-900/55" />
      )}
      {/* Blocks clicks on the page while the tour is open */}
      <div className="fixed inset-0" onClick={(e) => e.stopPropagation()} />

      <div
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="walkthrough-title"
        tabIndex={-1}
        className="fixed bg-white rounded-2xl border border-slate-200 shadow-2xl p-5 space-y-3 outline-none"
        style={cardStyle}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Step {index + 1} of {steps.length}
            </p>
            <h2 id="walkthrough-title" className="text-sm font-bold text-slate-900 mt-0.5">
              {step.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-900 hover:bg-slate-100 cursor-pointer"
            aria-label="Close walkthrough"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">{step.body}</p>

        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center space-x-1" aria-hidden="true">
            {steps.map((_, i) => (
              <span key={i} className={`h-1.5 rounded-full transition-all ${i === index ? "w-4 bg-slate-900" : "w-1.5 bg-slate-300"}`} />
            ))}
          </div>
          <div className="flex items-center space-x-2">
            {!isLast && (
              <button onClick={onClose} className="px-2.5 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 cursor-pointer">
                Skip tour
              </button>
            )}
            {index > 0 && (
              <button
                onClick={back}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
              >
                Back
              </button>
            )}
            <button
              onClick={next}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold cursor-pointer"
            >
              {isLast ? "Finish" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
