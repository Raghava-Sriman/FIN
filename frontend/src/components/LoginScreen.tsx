"use client";

import React, { useState } from "react";
import { AlertTriangle, ArrowRight, PlayCircle } from "lucide-react";

export const DEMO_USERNAME = "demo";
export const DEMO_PASSWORD = "demo1234";

type AuthAction = (username: string, password: string) => Promise<string | null>;

type Props = {
  /** Each returns an error message to show, or null on success */
  onLogin: AuthAction;
  onRegister: AuthAction;
  onDemo: () => Promise<string | null>;
};

export function LoginScreen({ onLogin, onRegister, onDemo }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"form" | "demo" | null>(null);

  const run = async (kind: "form" | "demo", action: () => Promise<string | null>) => {
    setBusy(kind);
    setError(null);
    const message = await action();
    if (message) {
      setError(message);
      setBusy(null);
    }
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    run("form", () => (mode === "login" ? onLogin : onRegister)(username, password));
  };

  const inputClass =
    "w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-hidden focus:border-slate-900 focus:ring-1 focus:ring-slate-900";

  return (
    <div className="min-h-screen bg-[#F9FAFB] text-[#111827] flex flex-col items-center justify-center py-10 px-4">
      <div className="text-center mb-6 space-y-1">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">FinSight</h1>
        <p className="text-sm text-slate-500">See where your money goes, from your own bank statements.</p>
      </div>

      <div className="w-full max-w-md space-y-4">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
          <div className="grid grid-cols-2 p-1 bg-slate-100 rounded-xl text-xs font-semibold" role="tablist">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                role="tab"
                aria-selected={mode === m}
                onClick={() => {
                  setMode(m);
                  setError(null);
                }}
                className={`py-2 rounded-lg transition cursor-pointer ${
                  mode === m ? "bg-white text-slate-900 shadow-xs font-bold" : "text-slate-500 hover:text-slate-900"
                }`}
              >
                {m === "login" ? "Log in" : "Sign up"}
              </button>
            ))}
          </div>

          {error && (
            <div role="alert" className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label htmlFor="auth-username" className="block text-xs font-bold text-slate-700 mb-1.5">
                Username
              </label>
              <input
                id="auth-username"
                type="text"
                autoComplete="username"
                autoCapitalize="none"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={inputClass}
                required
              />
              {mode === "register" && (
                <p className="text-[11px] text-slate-400 mt-1">3-32 characters: lowercase letters, numbers or underscores.</p>
              )}
            </div>
            <div>
              <label htmlFor="auth-password" className="block text-xs font-bold text-slate-700 mb-1.5">
                Password
              </label>
              <input
                id="auth-password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputClass}
                minLength={mode === "register" ? 8 : undefined}
                required
              />
              {mode === "register" && <p className="text-[11px] text-slate-400 mt-1">At least 8 characters.</p>}
            </div>
            <button
              type="submit"
              disabled={busy !== null}
              className="w-full py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
            >
              <span>{busy === "form" ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}</span>
              {busy !== "form" && <ArrowRight className="w-3.5 h-3.5" />}
            </button>
          </form>
        </div>

        <div className="bg-white rounded-2xl border border-indigo-200 shadow-sm p-5 space-y-3" aria-labelledby="demo-card-title">
          <div>
            <h2 id="demo-card-title" className="text-sm font-bold text-slate-900">Demo account</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Explore with a sample 1-year bank statement. Every demo gets its own private copy, deleted after 24 hours.
            </p>
          </div>
          <dl className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <dt className="text-[11px] text-slate-400">Username</dt>
              <dd className="font-mono font-semibold text-slate-900">{DEMO_USERNAME}</dd>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <dt className="text-[11px] text-slate-400">Password</dt>
              <dd className="font-mono font-semibold text-slate-900">{DEMO_PASSWORD}</dd>
            </div>
          </dl>
          <button
            onClick={() => run("demo", onDemo)}
            disabled={busy !== null}
            className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
          >
            <PlayCircle className="w-4 h-4" />
            <span>{busy === "demo" ? "Preparing your demo..." : "Try the demo"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
