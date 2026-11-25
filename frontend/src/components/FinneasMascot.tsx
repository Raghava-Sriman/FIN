"use client";

import React from "react";

interface FinneasMascotProps {
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  state?: "idle" | "thinking" | "happy";
  variant?: "welcome" | "chat";
  className?: string;
}

export const FinneasMascot: React.FC<FinneasMascotProps> = ({
  size = "md",
  state = "idle",
  variant,
  className = "",
}) => {
  const isWelcome = variant ? variant === "welcome" : size === "xl" || state === "happy";
  const gifSrc = isWelcome ? "/finneas-welcome.gif" : "/finneas.gif";

  const sizeClasses = {
    xs: "w-6 h-6",
    sm: "w-9 h-9",
    md: "w-12 h-12",
    lg: "w-20 h-20",
    xl: "w-20 h-20 sm:w-32 sm:h-32",
  }[size];

  const borderClasses = {
    xs: "border",
    sm: "border-[1.5px]",
    md: "border-2",
    lg: "border-2",
    xl: "border-2 sm:border-4",
  }[size];

  const thinkingBadgeSizes = {
    xs: "w-1.5 h-1.5 -bottom-0.5 -right-0.5",
    sm: "w-2.5 h-2.5 -bottom-0.5 -right-0.5",
    md: "w-3 h-3 -bottom-0.5 -right-0.5",
    lg: "w-4 h-4 -bottom-1 -right-1",
    xl: "w-5 h-5 -bottom-1 -right-1",
  }[size];

  return (
    <div
      className={`relative inline-flex items-center justify-center shrink-0 select-none aspect-square ${sizeClasses} ${className}`}
    >
      {/* THINKING GLOW RING AROUND CIRCLE */}
      {state === "thinking" && (
        <span
          className="absolute -inset-1 rounded-full bg-gradient-to-tr from-purple-600 via-indigo-500 to-amber-400 opacity-80 blur-[2px] animate-spin pointer-events-none"
          style={{ animationDuration: "2.5s" }}
        />
      )}

      {/* CIRCULAR CROPPED AVATAR CONTAINER */}
      <div
        className={`relative w-full h-full aspect-square rounded-full overflow-hidden ${borderClasses} border-purple-200/90 shadow-xs flex items-center justify-center transition-transform duration-200 ${
          state === "thinking" ? "scale-95 ring-2 ring-purple-500/80 ring-offset-1" : "hover:scale-105"
        }`}
        style={{ clipPath: "circle(50% at 50% 50%)", WebkitClipPath: "circle(50% at 50% 50%)" }}
      >
        <img
          src={gifSrc}
          alt={isWelcome ? "Finn-eas Waving Welcome" : "Finn-eas"}
          className="w-full h-full aspect-square object-cover object-center rounded-full select-none pointer-events-none block"
          style={{ clipPath: "circle(50% at 50% 50%)", WebkitClipPath: "circle(50% at 50% 50%)" }}
          loading="eager"
        />
      </div>

      {/* ACTIVE STATUS DOT WHEN THINKING */}
      {state === "thinking" && (
        <span className={`absolute flex ${thinkingBadgeSizes} pointer-events-none`}>
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-full w-full bg-purple-600 border border-white"></span>
        </span>
      )}
    </div>
  );
};
