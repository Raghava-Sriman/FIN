"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  TrendingUp,
  ShieldAlert,
  Target,
  Sparkles,
  Upload,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  ArrowRight,
  Umbrella,
  Wallet,
  Activity,
  CheckCircle2,
  RefreshCcw,
  LayoutDashboard,
  Calendar,
  FileText,
  Paperclip,
  Image as ImageIcon,
  Search,
  Trash2,
  HeartPulse,
  Flame,
  FileCheck2,
  Check,
  HelpCircle,
  Bot,
  Filter,
  ArrowUpDown,
  X,
  Car,
  Plus,
  ChevronRight,
  Info,
  ShieldCheck,
  Users,
  CheckCircle,
  ExternalLink,
  Lock,
  Building2,
  BadgePercent,
  Zap,
  LogOut,
  MessageSquarePlus,
  Send,
  MessageSquare,
  CornerDownLeft,
  User,
  UserPlus,
  KeyRound,
  PiggyBank,
  Plane,
  Shield,
  Crosshair,
  Award,
  Landmark,
  TrendingDown,
  Clock,
  Menu,
  Percent,
  Sliders,
  CreditCard,
  Utensils,
  Store,
  Repeat,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ReferenceLine,
} from "recharts";
import { FinneasMascot } from "@/components/FinneasMascot";
import { FinneasMessageContent } from "@/components/FinneasMessageContent";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

// Modern Institutional Fintech Palette (Stripe/Mercury)
const CATEGORY_COLORS = [
  "#2563EB", // Blue (Rent)
  "#E11D48", // Rose (Loan EMIs)
  "#0D9488", // Teal (Food & Dining)
  "#7C3AED", // Violet (Mutual Funds)
  "#059669", // Emerald (Fuel)
  "#DB2777", // Pink (Healthcare)
  "#D97706", // Amber (Domestic Help)
  "#64748B", // Slate (Others)
  "#4F46E5", // Indigo
  "#0284C7", // Sky
];

const MACRO_GROUPS = [
  {
    name: "Discretionary",
    items: [
      "Food Delivery & Dining",
      "Shopping & E-Commerce",
      "Entertainment & Outings",
      "Travel & Vacation",
      "Local Shopping & Services",
    ]
  },
  {
    name: "Variable Essentials",
    items: [
      "Groceries & Supplies",
      "Healthcare & Eyewear",
      "Education & Academic",
      "Fuel & Commute",
      "Ride Hailing & Auto",
      "Public Transit & Metro",
    ]
  },
  {
    name: "Fixed Expenses",
    items: [
      "Utilities & Bills",
      "Subscriptions",
      "Cloud & Tech Tools",
      "Insurance Premiums",
      "Loan EMIs & Rent",
    ]
  },
  {
    name: "Transfers & P2P",
    items: [
      "Transfer to Friends & Contacts"
    ]
  },
  {
    name: "Daily Micro-Spends",
    items: [
      "Local Vendor / Street Pay"
    ]
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "spend" | "goals" | "insurance" | "statements" | "merchants" | "finneas">("dashboard");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showFinneasSidebar, setShowFinneasSidebar] = useState(false);

  // Global state
  const [hasStatement, setHasStatement] = useState(false);
  const [overview, setOverview] = useState<any>(null);
  const [subscriptions, setSubscriptions] = useState<any>(null);
  const [insurance, setInsurance] = useState<any>(null);
  const [statementsInfo, setStatementsInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Merchant Intelligence state
  const [merchantItems, setMerchantItems] = useState<any[]>([]);
  const [merchantStats, setMerchantStats] = useState<{
    total: number;
    pending_review: number;
    verified: number;
    categories: string[];
    macro_map: Record<string, string>;
  }>({
    total: 0,
    pending_review: 0,
    verified: 0,
    categories: [],
    macro_map: {}
  });
  const [merchantFilter, setMerchantFilter] = useState<"all" | "pending" | "verified">("all");
  const [merchantSearch, setMerchantSearch] = useState("");
  const [isUpdatingMerchant, setIsUpdatingMerchant] = useState<string | null>(null);
  const [showReviewBanner, setShowReviewBanner] = useState(true);

  // Month drilldown state
  const [availableMonths, setAvailableMonths] = useState<string[]>([]);
  const [selectedMonth, setSelectedMonth] = useState<string>("");
  const [monthDetail, setMonthDetail] = useState<any>(null);
  const [monthLoading, setMonthLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [ledgerSortField, setLedgerSortField] = useState<"date" | "category" | "debit">("date");
  const [ledgerSortDir, setLedgerSortDir] = useState<"asc" | "desc">("desc");
  const [ledgerCategoryFilter, setLedgerCategoryFilter] = useState<string>("all");

  // AI Monthly Insights state
  const [monthInsightsMap, setMonthInsightsMap] = useState<Record<string, any>>({});
  const [isGeneratingInsights, setIsGeneratingInsights] = useState(false);
  const [insightsError, setInsightsError] = useState<string | null>(null);

  const handleGenerateInsights = async (month: string) => {
    if (!month) return;
    try {
      setIsGeneratingInsights(true);
      setInsightsError(null);
      const res = await fetch(`${API_BASE}/api/month-insights/${month}`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setMonthInsightsMap((prev) => ({ ...prev, [month]: data }));
      } else {
        setInsightsError("Failed to generate AI insights for this month.");
      }
    } catch (err: any) {
      console.error("AI Insights error:", err);
      setInsightsError("Network error while communicating with AI advisor.");
    } finally {
      setIsGeneratingInsights(false);
    }
  };

  const stripMarkdown = (text: any) => {
    if (!text) return "";
    return String(text).replace(/\*\*/g, "").trim();
  };

  const renderHighlightedText = (text: any, highlightColor?: string) => {
    if (!text) return null;
    if (typeof text !== "string") return String(text);
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return (
      <>
        {parts.map((part, i) => {
          if (part.startsWith("**") && part.endsWith("**")) {
            const inner = part.slice(2, -2).trim();
            return (
              <strong key={i} className={`font-semibold ${highlightColor || "text-slate-900"}`}>
                {inner}
              </strong>
            );
          }
          // Strip any stray or unmatched ** in regular text
          const cleanPart = part.replace(/\*\*/g, "");
          return <span key={i}>{cleanPart}</span>;
        })}
      </>
    );
  };

  const [isRefreshingAudit, setIsRefreshingAudit] = useState(false);

  const handleRefreshAudit = async () => {
    try {
      setIsRefreshingAudit(true);
      const res = await fetch(`${API_BASE}/api/strategic-audit`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setSubscriptions(data);
      }
    } catch (err) {
      console.error("Failed to refresh strategic audit:", err);
    } finally {
      setIsRefreshingAudit(false);
    }
  };

  const toggleSort = (field: "date" | "category" | "debit") => {
    if (ledgerSortField === field) {
      setLedgerSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setLedgerSortField(field);
      setLedgerSortDir(field === "category" ? "asc" : "desc");
    }
  };

  // Advanced Multi-Goal Planner & Simulator state
  const [goalsList, setGoalsList] = useState<any[]>([]);
  const [goalTemplates, setGoalTemplates] = useState<any[]>([]);
  const [cashflowContext, setCashflowContext] = useState<any>(null);
  const [activeGoalId, setActiveGoalId] = useState<string>("");
  const [simTargetAmount, setSimTargetAmount] = useState<number>(300000);
  const [simMonthlyAllocation, setSimMonthlyAllocation] = useState<number>(25000);
  const [simDiscretionaryCuts, setSimDiscretionaryCuts] = useState<Record<string, number>>({});
  const [simLumpsum, setSimLumpsum] = useState<number>(0);
  const [simReturnCagr, setSimReturnCagr] = useState<number>(7.0);
  const [simInflationRate, setSimInflationRate] = useState<number>(0.0);
  const [simResult, setSimResult] = useState<any>(null);
  const [goalsLoading, setGoalsLoading] = useState<boolean>(false);
  const [showCreateGoalModal, setShowCreateGoalModal] = useState<boolean>(false);
  const [newGoalForm, setNewGoalForm] = useState({
    title: "",
    category: "SAVINGS",
    target_amount: 250000,
    monthly_allocation: 20000,
    lumpsum_infusion: 0,
    target_return_cagr: 7.0,
    description: "",
  });

  // User Authentication & Account state
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authLoginForm, setAuthLoginForm] = useState({ username: "azizul", pin: "1234" });
  const [authRegisterForm, setAuthRegisterForm] = useState({ name: "", username: "", pin: "1234", email: "" });
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [availablePersonas, setAvailablePersonas] = useState<any[]>([]);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const getAuthHeaders = (userOverride?: string) => {
    const stored = typeof window !== "undefined" ? (localStorage.getItem("finsight_user") || localStorage.getItem("finman_user")) : null;
    const storedUser = stored ? JSON.parse(stored) : null;
    const u = userOverride || currentUser?.username || storedUser?.username || "azizul";
    return {
      "X-User-ID": u,
    };
  };

  // Comprehensive Insurance Manager state
  const [hlvIncome, setHlvIncome] = useState(1260000);
  const [hlvMultiplier, setHlvMultiplier] = useState(12);
  const [hlvLoans, setHlvLoans] = useState(680000);
  const [hlvAssets, setHlvAssets] = useState(500000);
  const [hlvDependents, setHlvDependents] = useState(2);

  const [insurancePortfolio, setInsurancePortfolio] = useState<any>(null);
  const [insurancePersonas, setInsurancePersonas] = useState<any[]>([]);
  const [activePersonaId, setActivePersonaId] = useState<string | null>(null);
  const [insuranceLoading, setInsuranceLoading] = useState(false);
  const [insuranceAiLoading, setInsuranceAiLoading] = useState(false);
  const [aiRecommendations, setAiRecommendations] = useState<any>(null);
  const [insuranceCatalog, setInsuranceCatalog] = useState<any[]>([]);
  const [policyFilter, setPolicyFilter] = useState<"ALL" | "LIFE" | "HEALTH" | "MOTOR" | "PERSONAL_ACCIDENT">("ALL");
  const [showAddPolicyModal, setShowAddPolicyModal] = useState(false);
  const [showCatalogDrawer, setShowCatalogDrawer] = useState(false);
  const [catalogFilter, setCatalogFilter] = useState<string>("ALL");
  const [adoptingRecIdx, setAdoptingRecIdx] = useState<number | null>(null);

  // Finneas Chat Agent state
  const [finneasThreads, setFinneasThreads] = useState<any[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [finneasMessages, setFinneasMessages] = useState<any[]>([]);
  const [finneasLoading, setFinneasLoading] = useState(false);
  const [finneasInput, setFinneasInput] = useState("");
  const [finneasThreadsLoading, setFinneasThreadsLoading] = useState(false);
  const [finneasAttachments, setFinneasAttachments] = useState<
    Array<{
      file: File;
      name: string;
      type: string;
      size: number;
      previewUrl?: string;
    }>
  >([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const [addPolicyForm, setAddPolicyForm] = useState({
    category: "HEALTH",
    insurer_name: "",
    plan_name: "",
    sum_insured: 500000,
    annual_premium: 0,
    source: "EMPLOYER_GMC",
    is_employer_provided: true,
    covered_members: "Self",
    has_room_rent_capping: false,
    notes: ""
  });

  // Derived insurance calculations
  const hlvRequiredCover = Math.max(0, hlvIncome * hlvMultiplier + hlvLoans - hlvAssets);
  const detectedCover = insurancePortfolio?.metrics?.total_life_cover ?? (insurance?.life_insurance?.detected_cover || 0);
  const hlvGap = Math.max(0, hlvRequiredCover - detectedCover);
  const estTermAnnualPremium = Math.round((hlvRequiredCover / 10000000) * 9200);
  const estTermMonthlyPremium = Math.round(estTermAnnualPremium / 12);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  // Toggle macro vs granular
  const [breakdownView, setBreakdownView] = useState<"macro" | "granular">("granular");

  const fetchInsuranceData = async (userOverride?: string) => {
    const stored = typeof window !== "undefined" ? (localStorage.getItem("finsight_user") || localStorage.getItem("finman_user")) : null;
    const storedUser = stored ? JSON.parse(stored) : null;
    const targetUser = userOverride || currentUser?.username || storedUser?.username || "azizul";
    const headers = { "X-User-ID": targetUser };
    try {
      const [portRes, persRes, catRes] = await Promise.all([
        fetch(`${API_BASE}/api/insurance/portfolio`, { headers }),
        fetch(`${API_BASE}/api/insurance/personas`, { headers }),
        fetch(`${API_BASE}/api/insurance/catalog`, { headers }),
      ]);
      const portData = portRes.ok ? await portRes.json() : null;
      const persData = persRes.ok ? await persRes.json() : { personas: [] };
      const catData = catRes.ok ? await catRes.json() : { products: [] };

      if (portData) {
        setInsurancePortfolio(portData);
        setActivePersonaId(portData?.active_persona_id || null);
        if (portData?.metrics) {
          setHlvIncome(portData.metrics.annual_income ?? 1260000);
          setHlvLoans(portData.metrics.outstanding_loans ?? 0);
          setHlvAssets(portData.metrics.liquid_assets ?? 0);
          setHlvDependents(portData.metrics.dependents_count ?? 2);
          setHlvMultiplier(portData.metrics.income_multiplier ?? 12);
        }
      }
      setInsurancePersonas(persData?.personas || []);
      setInsuranceCatalog(catData?.products || []);
    } catch (err) {
      console.warn("Insurance portfolio fetch notice:", err);
    }
  };

  const fetchGlobalData = async (showFullSpinner = false, userOverride?: string) => {
    const stored = typeof window !== "undefined" ? (localStorage.getItem("finsight_user") || localStorage.getItem("finman_user")) : null;
    const storedUser = stored ? JSON.parse(stored) : null;
    const targetUser = userOverride || currentUser?.username || storedUser?.username || "azizul";
    const headers = { "X-User-ID": targetUser };
    try {
      if (showFullSpinner) setLoading(true);
      const ovRes = await fetch(`${API_BASE}/api/overview`, { headers });
      if (!ovRes.ok) return;
      const ovData = await ovRes.json();

      if (!ovData.has_statement) {
        setHasStatement(false);
        setOverview(null);
        setSubscriptions(null);
        setStatementsInfo(null);
        setAvailableMonths([]);
        setSelectedMonth("");
        setMonthDetail(null);
        await fetchInsuranceData(targetUser);
        return;
      }

      setHasStatement(true);
      setOverview(ovData);

      const [subRes, insRes, mRes, stmtRes, dictRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/api/subscriptions`, { headers }),
        fetch(`${API_BASE}/api/insurance`, { headers }),
        fetch(`${API_BASE}/api/months`, { headers }),
        fetch(`${API_BASE}/api/statements-list`, { headers }),
        fetch(`${API_BASE}/api/merchant-dictionary`, { headers }),
        fetch(`${API_BASE}/api/merchant-dictionary/stats`, { headers }),
      ]);

      const subData = subRes.ok ? await subRes.json() : null;
      const insData = insRes.ok ? await insRes.json() : null;
      const mData = mRes.ok ? await mRes.json() : { months: [] };
      const stmtData = stmtRes.ok ? await stmtRes.json() : null;
      const dictData = dictRes.ok ? await dictRes.json() : { merchants: [] };
      const statsData = statsRes.ok ? await statsRes.json() : { total: 0, pending_review: 0, verified: 0, categories: [], macro_map: {} };

      if (subData) setSubscriptions(subData);
      if (insData) {
        setInsurance(insData);
        if (insData?.life_insurance?.annual_income) {
          setHlvIncome(insData.life_insurance.annual_income);
        }
      }
      if (stmtData) setStatementsInfo(stmtData);
      setMerchantItems(dictData.merchants || []);
      setMerchantStats(statsData);
      setAvailableMonths(mData.months || []);
      if (mData.months && mData.months.length > 0) {
        setSelectedMonth(mData.months[0]);
      }
      // Re-fetch insurance portfolio whenever global ledger updates
      await fetchInsuranceData(targetUser);
    } catch (err) {
      console.warn("Global data fetch notice:", err);
    } finally {
      if (showFullSpinner) setLoading(false);
    }
  };

  const fetchMerchantData = async () => {
    try {
      const headers = getAuthHeaders();
      const [dictRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/api/merchant-dictionary`, { headers }),
        fetch(`${API_BASE}/api/merchant-dictionary/stats`, { headers }),
      ]);
      const dictData = await dictRes.json();
      const statsData = await statsRes.json();
      setMerchantItems(dictData.merchants || []);
      setMerchantStats(statsData);
    } catch (err) {
      console.error("Failed to load merchant dictionary:", err);
    }
  };

  const handleUpdateMerchantCategory = async (merchantKey: string, newSubCategory: string) => {
    let inferredMacro = "Discretionary";
    for (const grp of MACRO_GROUPS) {
      if (grp.items.includes(newSubCategory)) {
        inferredMacro = grp.name;
        break;
      }
    }

    setMerchantItems((prev) =>
      prev.map((m) => {
        if (m.merchant_key === merchantKey) {
          return {
            ...m,
            sub_category: newSubCategory,
            category: inferredMacro,
            verified: true,
            needs_review: false,
            confidence: 1.0,
            source: "user",
            reasoning: "Manually verified & assigned by you"
          };
        }
        return m;
      })
    );

    setMerchantStats((prev) => {
      const target = merchantItems.find((m) => m.merchant_key === merchantKey);
      const wasPending = target ? (target.needs_review || !target.verified) : false;
      return {
        ...prev,
        pending_review: wasPending ? Math.max(0, prev.pending_review - 1) : prev.pending_review,
        verified: wasPending ? prev.verified + 1 : prev.verified,
      };
    });

    try {
      setIsUpdatingMerchant(merchantKey);
      const res = await fetch(`${API_BASE}/api/merchant-dictionary/${encodeURIComponent(merchantKey)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({ sub_category: newSubCategory, category: inferredMacro })
      });
      if (res.ok) {
        fetchGlobalData(false);
        if (selectedMonth) {
          fetchMonthDetail(selectedMonth);
        }
      }
    } catch (err) {
      console.error("Failed to update merchant:", err);
      fetchMerchantData();
    } finally {
      setIsUpdatingMerchant(null);
    }
  };

  const handleApproveMerchant = async (merchantKey: string) => {
    setMerchantItems((prev) =>
      prev.map((m) => {
        if (m.merchant_key === merchantKey) {
          return {
            ...m,
            verified: true,
            needs_review: false,
          };
        }
        return m;
      })
    );

    setMerchantStats((prev) => ({
      ...prev,
      pending_review: Math.max(0, prev.pending_review - 1),
      verified: prev.verified + 1,
    }));

    try {
      setIsUpdatingMerchant(merchantKey);
      const res = await fetch(`${API_BASE}/api/merchant-dictionary/${encodeURIComponent(merchantKey)}/approve`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        fetchGlobalData(false);
      }
    } catch (err) {
      console.error("Failed to approve merchant:", err);
      fetchMerchantData();
    } finally {
      setIsUpdatingMerchant(null);
    }
  };

  const handleApproveAllMerchants = async () => {
    setMerchantItems((prev) =>
      prev.map((m) => ({
        ...m,
        verified: true,
        needs_review: false,
      }))
    );

    setMerchantStats((prev) => ({
      ...prev,
      pending_review: 0,
      verified: prev.total,
    }));

    try {
      const res = await fetch(`${API_BASE}/api/merchant-dictionary/approve-all`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        fetchGlobalData(false);
        if (selectedMonth) {
          fetchMonthDetail(selectedMonth);
        }
      }
    } catch (err) {
      console.error("Failed to approve all merchants:", err);
      fetchMerchantData();
    }
  };

  const handleResetMerchantCache = async () => {
    if (!confirm("Clear all merchant cache and re-classify all transactions with Gemini AI?")) {
      return;
    }
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/merchant-dictionary/reset`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        await Promise.all([fetchMerchantData(), fetchGlobalData()]);
        if (selectedMonth) {
          await fetchMonthDetail(selectedMonth);
        }
      }
    } catch (err) {
      console.error("Failed to reset merchant cache:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchMonthDetail = async (m: string) => {
    if (!m) return;
    try {
      setMonthLoading(true);
      const res = await fetch(`${API_BASE}/api/month-detail/${m}`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setMonthDetail(data);
      }
    } catch (err) {
      // Retry once after brief delay in case backend was reloading
      try {
        await new Promise((r) => setTimeout(r, 400));
        const retryRes = await fetch(`${API_BASE}/api/month-detail/${m}`, {
          headers: getAuthHeaders(),
        });
        if (retryRes.ok) {
          const retryData = await retryRes.json();
          setMonthDetail(retryData);
        }
      } catch (retryErr) {
        console.warn("Month detail fetch notice:", retryErr);
      }
    } finally {
      setMonthLoading(false);
    }
  };

  const fetchGoalsData = async (userOverride?: string) => {
    try {
      setGoalsLoading(true);
      const res = await fetch(`${API_BASE}/api/goals`, {
        headers: getAuthHeaders(userOverride),
      });
      if (res.ok) {
        const data = await res.json();
        setGoalsList(data.goals || []);
        setCashflowContext(data.cashflow_context || null);
        setGoalTemplates(data.templates || []);

        // If no active goal or goals changed, sync active goal
        if (data.goals && data.goals.length > 0) {
          const currentActive = data.goals.find((g: any) => g.id === activeGoalId) || data.goals[0];
          setActiveGoalId(currentActive.id);
          setSimTargetAmount(currentActive.target_amount);
          setSimMonthlyAllocation(currentActive.monthly_allocation);
          setSimLumpsum(currentActive.lumpsum_infusion || 0);
          setSimReturnCagr(currentActive.target_return_cagr || 7.0);
        } else {
          setActiveGoalId("");
        }
      }
    } catch (err) {
      console.warn("Goals data fetch notice:", err);
    } finally {
      setGoalsLoading(false);
    }
  };

  const runAdvancedGoalSimulation = async (overrides?: any) => {
    try {
      const payload = {
        target_amount: overrides?.target_amount ?? simTargetAmount,
        monthly_allocation: overrides?.monthly_allocation ?? simMonthlyAllocation,
        discretionary_cuts: overrides?.discretionary_cuts ?? simDiscretionaryCuts,
        lumpsum_infusion: overrides?.lumpsum_infusion ?? simLumpsum,
        return_cagr: overrides?.return_cagr ?? simReturnCagr,
        inflation_rate: overrides?.inflation_rate ?? simInflationRate,
      };

      const res = await fetch(`${API_BASE}/api/goals/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setSimResult(data);
      }
    } catch (err) {
      console.warn("Simulation notice:", err);
    }
  };

  const handleSelectGoal = (goal: any) => {
    setActiveGoalId(goal.id);
    setSimTargetAmount(goal.target_amount);
    setSimMonthlyAllocation(goal.monthly_allocation);
    setSimLumpsum(goal.lumpsum_infusion || 0);
    setSimReturnCagr(goal.target_return_cagr || 7.0);
  };

  const handleSelectTemplate = (tpl: any) => {
    setActiveGoalId(tpl.id || "");
    setSimTargetAmount(tpl.target_amount);
    setSimMonthlyAllocation(tpl.monthly_allocation);
    setSimLumpsum(tpl.lumpsum_infusion || 0);
    setSimReturnCagr(tpl.target_return_cagr || 7.0);
  };

  const handleCutChange = (categoryName: string, cutVal: number) => {
    setSimDiscretionaryCuts((prev) => {
      const next = { ...prev };
      if (cutVal <= 0) {
        delete next[categoryName];
      } else {
        next[categoryName] = cutVal;
      }
      return next;
    });
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/goals`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify(newGoalForm),
      });
      if (res.ok) {
        setShowCreateGoalModal(false);
        setNewGoalForm({
          title: "",
          category: "SAVINGS",
          target_amount: 250000,
          monthly_allocation: 20000,
          lumpsum_infusion: 0,
          target_return_cagr: 7.0,
          description: "",
        });
        await fetchGoalsData();
      }
    } catch (err) {
      console.error("Error creating goal:", err);
    }
  };

  const handleDeleteGoal = async (goalId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/goals/${goalId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        await fetchGoalsData();
      }
    } catch (err) {
      console.error("Error deleting goal:", err);
    }
  };

  const handleRecalculateHlv = async (
    newIncome?: number,
    newLoans?: number,
    newAssets?: number,
    newDeps?: number,
    newMult?: number
  ) => {
    const inc = newIncome !== undefined ? newIncome : hlvIncome;
    const lns = newLoans !== undefined ? newLoans : hlvLoans;
    const ast = newAssets !== undefined ? newAssets : hlvAssets;
    const deps = newDeps !== undefined ? newDeps : hlvDependents;
    const mult = newMult !== undefined ? newMult : hlvMultiplier;

    try {
      const res = await fetch(`${API_BASE}/api/insurance/portfolio`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({
          annual_income: inc,
          outstanding_loans: lns,
          liquid_assets: ast,
          dependents_count: deps,
          income_multiplier: mult,
        }),
      });
      const data = await res.json();
      setInsurancePortfolio(data);
    } catch (err) {
      console.error("Error recalculating HLV:", err);
    }
  };

  const handleGenerateAiRecommendations = async () => {
    try {
      setInsuranceAiLoading(true);
      const res = await fetch(`${API_BASE}/api/insurance/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({
          annual_income: hlvIncome,
          outstanding_loans: hlvLoans,
          liquid_assets: hlvAssets,
          dependents_count: hlvDependents,
          income_multiplier: hlvMultiplier,
        }),
      });
      const data = await res.json();
      setAiRecommendations(data.ai_recommendations);
    } catch (err) {
      console.error("Error generating AI recommendations:", err);
    } finally {
      setInsuranceAiLoading(false);
    }
  };

  const isRecAlreadyAdopted = (rec: any) => {
    if (!insurancePortfolio?.unified_policies) return false;
    return insurancePortfolio.unified_policies.some((p: any) => {
      if (p.notes && rec.action_title && p.notes.includes(rec.action_title)) return true;
      if (p.notes && rec.matched_product_name && p.notes.includes(rec.matched_product_name)) return true;

      const rawCat = (rec.category || "").toUpperCase();
      let cat = "OTHER";
      if (rawCat.includes("LIFE")) cat = "LIFE";
      else if (rawCat.includes("HEALTH")) cat = "HEALTH";
      else if (rawCat.includes("MOTOR")) cat = "MOTOR";
      else if (rawCat.includes("ACCIDENT")) cat = "PERSONAL_ACCIDENT";

      if (p.category === cat && p.source === "AI_RECOMMENDED") {
        if (rec.matched_product_id && p.id?.includes(rec.matched_product_id)) return true;
        if (p.insurer_name && rec.matched_product_name?.toLowerCase().includes(p.insurer_name.toLowerCase())) return true;
        if (p.plan_name && rec.matched_product_name?.toLowerCase().includes(p.plan_name.toLowerCase())) return true;
      }
      return false;
    });
  };

  const handleAdoptRecommendation = async (rec: any, idx: number) => {
    try {
      setAdoptingRecIdx(idx);

      const matchedCatalog = insuranceCatalog.find((p) => p.id === rec.matched_product_id);
      let insurer = matchedCatalog?.insurer;
      let plan = matchedCatalog?.product_name;

      if (!insurer || !plan) {
        if (rec.matched_product_name && rec.matched_product_name.includes(" - ")) {
          const parts = rec.matched_product_name.split(" - ");
          insurer = parts[0].trim();
          plan = parts.slice(1).join(" - ").trim();
        } else {
          insurer = rec.matched_product_name || "IRDAI Insurer";
          plan = rec.action_title || "Recommended Cover";
        }
      }

      const rawCat = (rec.category || "OTHER").toUpperCase();
      let cat = "OTHER";
      if (rawCat.includes("LIFE")) cat = "LIFE";
      else if (rawCat.includes("HEALTH")) cat = "HEALTH";
      else if (rawCat.includes("MOTOR")) cat = "MOTOR";
      else if (rawCat.includes("ACCIDENT")) cat = "PERSONAL_ACCIDENT";

      const payload = {
        category: cat,
        insurer_name: insurer,
        plan_name: plan,
        sum_insured: Number(rec.recommended_sum_insured || 0),
        annual_premium: Number(rec.estimated_annual_cost || 0),
        source: "AI_RECOMMENDED",
        is_employer_provided: Boolean(rec.is_super_topup_bridge),
        covered_members: ["Self"],
        has_room_rent_capping: false,
        notes: `Adopted from AI Recommendation: ${rec.action_title}`,
      };

      const res = await fetch(`${API_BASE}/api/insurance/declare`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        await fetchInsuranceData();
      }
    } catch (err) {
      console.error("Error adopting AI recommendation:", err);
    } finally {
      setAdoptingRecIdx(null);
    }
  };

  const handleAddPolicySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addPolicyForm.insurer_name.trim() || !addPolicyForm.plan_name.trim()) return;

    try {
      const payload = {
        category: addPolicyForm.category,
        insurer_name: addPolicyForm.insurer_name.trim(),
        plan_name: addPolicyForm.plan_name.trim(),
        sum_insured: Number(addPolicyForm.sum_insured),
        annual_premium: Number(addPolicyForm.annual_premium || 0),
        source: addPolicyForm.source,
        is_employer_provided: addPolicyForm.source === "EMPLOYER_GMC",
        covered_members: addPolicyForm.covered_members
          .split(",")
          .map((m) => m.trim())
          .filter(Boolean),
        has_room_rent_capping: addPolicyForm.has_room_rent_capping,
        notes: addPolicyForm.notes.trim(),
      };

      await fetch(`${API_BASE}/api/insurance/declare`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify(payload),
      });

      setShowAddPolicyModal(false);
      setAddPolicyForm({
        category: "HEALTH",
        insurer_name: "",
        plan_name: "",
        sum_insured: 500000,
        annual_premium: 0,
        source: "EMPLOYER_GMC",
        is_employer_provided: true,
        covered_members: "Self",
        has_room_rent_capping: false,
        notes: "",
      });

      await fetchInsuranceData();
    } catch (err) {
      console.error("Error adding declared policy:", err);
    }
  };

  const handleDeletePolicy = async (policyId: string) => {
    try {
      await fetch(`${API_BASE}/api/insurance/declare/${policyId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      await fetchInsuranceData();
    } catch (err) {
      console.error("Error deleting declared policy:", err);
    }
  };

  // Finneas Agent Handlers
  const fetchFinneasThreads = async (userOverride?: string) => {
    try {
      setFinneasThreadsLoading(true);
      const res = await fetch(`${API_BASE}/api/finneas/threads`, {
        headers: getAuthHeaders(userOverride),
      });
      if (res.ok) {
        const data = await res.json();
        const threads = data.threads || [];
        setFinneasThreads(threads);
        if (threads.length > 0) {
          const currentExists = threads.some((t: any) => t.id === activeThreadId);
          if (!currentExists) {
            selectThread(threads[0].id, threads, userOverride);
          }
        } else {
          setActiveThreadId(null);
          setFinneasMessages([]);
        }
      }
    } catch (err) {
      console.error("Error fetching Finneas threads:", err);
    } finally {
      setFinneasThreadsLoading(false);
    }
  };

  const selectThread = async (threadId: string, threadList?: any[], userOverride?: string) => {
    setActiveThreadId(threadId);
    const list = threadList || finneasThreads;
    const found = list.find((t) => t.id === threadId);
    if (found && found.messages) {
      setFinneasMessages(found.messages);
    } else {
      try {
        const res = await fetch(`${API_BASE}/api/finneas/threads/${threadId}`, {
          headers: getAuthHeaders(userOverride),
        });
        if (res.ok) {
          const data = await res.json();
          setFinneasMessages(data.thread?.messages || []);
        }
      } catch (err) {
        console.error("Error fetching thread messages:", err);
      }
    }
  };

  const handleCreateNewThread = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/finneas/threads`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({ title: "New Financial Discussion" }),
      });
      if (res.ok) {
        const data = await res.json();
        const newTh = data.thread;
        setFinneasThreads((prev) => [newTh, ...prev]);
        setActiveThreadId(newTh.id);
        setFinneasMessages([]);
      }
    } catch (err) {
      console.error("Error creating new thread:", err);
    }
  };

  const handleDeleteThread = async (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`${API_BASE}/api/finneas/threads/${threadId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      const updated = finneasThreads.filter((t) => t.id !== threadId);
      setFinneasThreads(updated);
      if (activeThreadId === threadId) {
        if (updated.length > 0) {
          selectThread(updated[0].id, updated);
        } else {
          setActiveThreadId(null);
          setFinneasMessages([]);
        }
      }
    } catch (err) {
      console.error("Error deleting thread:", err);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const files = Array.from(e.target.files);
    const newItems: typeof finneasAttachments = [];

    for (const f of files) {
      if (f.size > 15 * 1024 * 1024) {
        alert(`"${f.name}" exceeds the 15MB limit. Please upload a smaller file.`);
        continue;
      }
      const isImg = f.type.startsWith("image/");
      const previewUrl = isImg ? URL.createObjectURL(f) : undefined;
      newItems.push({
        file: f,
        name: f.name,
        type: f.type || (f.name.endsWith(".pdf") ? "application/pdf" : "application/octet-stream"),
        size: f.size,
        previewUrl,
      });
    }

    setFinneasAttachments((prev) => [...prev, ...newItems].slice(0, 5));
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleRemoveAttachment = (idx: number) => {
    setFinneasAttachments((prev) => {
      const target = prev[idx];
      if (target?.previewUrl) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((_, i) => i !== idx);
    });
  };

  const handleSendFinneasMessage = async (customPrompt?: string) => {
    const textToSend = (customPrompt || finneasInput).trim();
    if ((!textToSend && finneasAttachments.length === 0) || finneasLoading) return;

    const attachmentsToSend = [...finneasAttachments];
    setFinneasInput("");
    setFinneasAttachments([]);
    setFinneasLoading(true);

    // Convert attachments to base64
    const convertedAttachments: Array<{
      name: string;
      type: string;
      size: number;
      data: string;
      previewUrl?: string;
    }> = [];

    for (const att of attachmentsToSend) {
      try {
        const base64Data = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(att.file);
        });
        convertedAttachments.push({
          name: att.name,
          type: att.type,
          size: att.size,
          data: base64Data,
          previewUrl: att.previewUrl,
        });
      } catch (err) {
        console.error("Failed to read file:", att.name, err);
      }
    }

    const tempUserMsg = {
      id: `temp_u_${Date.now()}`,
      role: "user",
      content:
        textToSend ||
        (convertedAttachments.length > 0
          ? `Attached ${convertedAttachments.length} document${convertedAttachments.length > 1 ? "s" : ""}: ${convertedAttachments.map((a) => a.name).join(", ")}`
          : ""),
      attachments: convertedAttachments.map((a) => ({
        id: `att_${Math.random().toString(36).substring(2, 9)}`,
        name: a.name,
        type: a.type,
        size: a.size,
        url: a.previewUrl || "",
        previewUrl: a.previewUrl,
      })),
      timestamp: new Date().toISOString(),
    };
    setFinneasMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await fetch(`${API_BASE}/api/finneas/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({
          thread_id: activeThreadId,
          message: textToSend,
          attachments: convertedAttachments.map((a) => ({
            name: a.name,
            type: a.type,
            size: a.size,
            data: a.data,
          })),
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (!activeThreadId && data.thread_id) {
          setActiveThreadId(data.thread_id);
        }

        setFinneasMessages((prev) => {
          const withoutTemp = prev.filter((m) => m.id !== tempUserMsg.id);
          return [...withoutTemp, data.user_message, data.assistant_message];
        });

        const thRes = await fetch(`${API_BASE}/api/finneas/threads`, {
          headers: getAuthHeaders(),
        });
        if (thRes.ok) {
          const thData = await thRes.json();
          setFinneasThreads(thData.threads || []);
        }
      }
    } catch (err) {
      console.error("Error sending message to Finneas:", err);
    } finally {
      setFinneasLoading(false);
    }
  };

  // Profile Authentication Handlers
  const handleLogin = async (usernameOverride?: string, pinOverride?: string) => {
    const un = (usernameOverride || authLoginForm.username).trim().toLowerCase();
    const pin = pinOverride || authLoginForm.pin;
    if (!un || !pin) {
      setAuthError("Please provide both username and PIN.");
      return;
    }
    setAuthLoading(true);
    setAuthError(null);
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: un, pin }),
      });
      const data = await res.json();
      if (!res.ok || data.status !== "success") {
        setAuthError(data.detail || "Authentication failed. Check your username and PIN.");
        return;
      }
      localStorage.setItem("finman_user", JSON.stringify(data.user));
      setCurrentUser(data.user);
      setActiveThreadId(null);
      setFinneasMessages([]);
      setFinneasThreads([]);
      await Promise.all([
        fetchGlobalData(false, data.user.username),
        fetchInsuranceData(data.user.username),
        fetchGoalsData(data.user.username),
        fetchFinneasThreads(data.user.username),
      ]);
      setActiveTab("dashboard");
    } catch (err: any) {
      console.error("Login error:", err);
      setAuthError(err.message || "Could not connect to authentication server.");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const { name, username, pin, email } = authRegisterForm;
    if (!name.trim() || !username.trim() || !pin.trim()) {
      setAuthError("Please fill in name, username, and PIN.");
      return;
    }
    setAuthLoading(true);
    setAuthError(null);
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          username: username.trim().toLowerCase(),
          pin: pin.trim(),
          email: email.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok || data.status !== "success") {
        setAuthError(data.detail || "Registration failed.");
        return;
      }
      localStorage.setItem("finman_user", JSON.stringify(data.user));
      setCurrentUser(data.user);
      setActiveThreadId(null);
      setFinneasMessages([]);
      setFinneasThreads([]);
      await Promise.all([
        fetchGlobalData(false, data.user.username),
        fetchInsuranceData(data.user.username),
        fetchGoalsData(data.user.username),
        fetchFinneasThreads(data.user.username),
      ]);
      setActiveTab("statements");
    } catch (err: any) {
      console.error("Registration error:", err);
      setAuthError(err.message || "Failed to create account.");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem("finman_user");
    setCurrentUser(null);
    setOverview(null);
    setHasStatement(false);
    setSubscriptions(null);
    setInsurance(null);
    setInsurancePortfolio(null);
    setStatementsInfo(null);
    setMerchantItems([]);
    setMerchantStats({ total: 0, pending_review: 0, verified: 0, categories: [], macro_map: {} });
    setAvailableMonths([]);
    setSelectedMonth("");
    setMonthDetail(null);
    setFinneasThreads([]);
    setFinneasMessages([]);
    setActiveThreadId(null);
    setFinneasInput("");
    setActiveTab("dashboard");
  };

  // Mount effect: load personas and restore active user session
  useEffect(() => {
    let isMounted = true;
    const safetyTimer = setTimeout(() => {
      if (isMounted) {
        setAuthChecking(false);
      }
    }, 2500);

    const initAuth = async () => {
      try {
        setAuthChecking(true);
        const pRes = await fetch(`${API_BASE}/api/auth/personas`).catch(() => null);
        if (pRes && pRes.ok) {
          const pData = await pRes.json().catch(() => ({ personas: [] }));
          if (isMounted) setAvailablePersonas(pData.personas || []);
        }

        const saved = typeof window !== "undefined" ? localStorage.getItem("finman_user") : null;
        let activeUser = null;
        if (saved) {
          try {
            activeUser = JSON.parse(saved);
          } catch {
            activeUser = null;
          }
        }

        // Auto-hydrate Azizul on initial load if no session exists yet
        if (!activeUser) {
          try {
            const loginRes = await fetch(`${API_BASE}/api/auth/login`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ username: "azizul", pin: "1234" }),
            });
            if (loginRes.ok) {
              const loginData = await loginRes.json();
              activeUser = loginData.user;
              if (typeof window !== "undefined") {
                localStorage.setItem("finman_user", JSON.stringify(activeUser));
              }
            }
          } catch (e) {
            console.error("Auto-login error:", e);
          }
        }

        if (isMounted) {
          if (activeUser) {
            setCurrentUser(activeUser);
            setAuthChecking(false);
            // Fetch initial user data without stalling screen mount
            Promise.all([
              fetchGlobalData(false, activeUser.username),
              fetchInsuranceData(activeUser.username),
              fetchGoalsData(activeUser.username),
              fetchFinneasThreads(activeUser.username),
            ]).catch((err) => console.error("Initial data load error:", err));
          } else {
            setAuthChecking(false);
          }
        }
      } catch (err) {
        console.error("Auth init error:", err);
      } finally {
        if (isMounted) {
          setAuthChecking(false);
          setLoading(false);
        }
      }
    };

    initAuth();

    return () => {
      isMounted = false;
      clearTimeout(safetyTimer);
    };
  }, []);

  // Synchronize and isolate Finneas threads whenever the active user changes
  useEffect(() => {
    if (currentUser?.username) {
      setActiveThreadId(null);
      setFinneasMessages([]);
      setFinneasThreads([]);
      fetchFinneasThreads(currentUser.username);
    } else {
      setActiveThreadId(null);
      setFinneasMessages([]);
      setFinneasThreads([]);
    }
  }, [currentUser?.username]);

  useEffect(() => {
    if (selectedMonth && hasStatement) {
      fetchMonthDetail(selectedMonth);
    }
  }, [selectedMonth, hasStatement]);

  useEffect(() => {
    if (activeTab === "goals") {
      fetchGoalsData();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === "insurance") {
      fetchInsuranceData();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === "finneas" && currentUser?.username) {
      fetchFinneasThreads(currentUser.username);
    }
  }, [activeTab, currentUser?.username]);

  useEffect(() => {
    if (activeTab === "finneas") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [finneasMessages, finneasLoading, activeTab]);

  useEffect(() => {
    runAdvancedGoalSimulation();
  }, [simTargetAmount, simMonthlyAllocation, simDiscretionaryCuts, simLumpsum, simReturnCagr, simInflationRate]);

  const [isDragging, setIsDragging] = useState(false);

  const uploadFiles = async (files: File[]) => {
    if (!files || files.length === 0) return;
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    try {
      setUploading(true);
      const label = files.length === 1 ? files[0].name : `${files.length} statement files`;
      setUploadStatus(`Parsing and merging ${label}...`);
      const res = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      });
      const data = await res.json();
      if (!res.ok || data.status === "error") {
        throw new Error(data.message || data.detail || "Failed to parse statements");
      }
      setUploadStatus(`Successfully merged ${data.files_count || files.length} statement file(s) with ${data.transactions_parsed} transactions.`);
      await Promise.all([
        fetchGlobalData(false),
        fetchInsuranceData()
      ]);
      setActiveTab("dashboard");
    } catch (err: any) {
      setUploadStatus(err.message || "Failed to parse statement.");
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    uploadFiles(Array.from(e.target.files));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleLoadDemo = async () => {
    await fetch(`${API_BASE}/api/load-demo`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    await Promise.all([
      fetchGlobalData(false),
      fetchInsuranceData()
    ]);
    setActiveTab("dashboard");
  };

  const handleClearStatement = async () => {
    await fetch(`${API_BASE}/api/clear-statement`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    await Promise.all([
      fetchGlobalData(false),
      fetchInsuranceData()
    ]);
    setActiveTab("statements");
  };

  const handleUnloadSingleStatement = async (statementId: string, filename: string) => {
    try {
      setUploading(true);
      setUploadStatus(`Removing ${filename} and re-stitching ledger...`);
      const res = await fetch(`${API_BASE}/api/statements/${statementId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      if (!data.has_statement) {
        setHasStatement(false);
        setActiveTab("dashboard");
      }
      await Promise.all([
        fetchGlobalData(false),
        fetchInsuranceData()
      ]);
      setUploadStatus(`Successfully removed ${filename}.`);
    } catch (err) {
      console.error("Failed to delete statement:", err);
      setUploadStatus("Failed to remove statement.");
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 4000);
    }
  };

  if (authChecking) {
    return (
      <div className="min-h-screen bg-[#F9FAFB] flex flex-col items-center justify-center p-6">
        <div className="w-8 h-8 rounded-full border-2 border-slate-300 border-t-slate-900 animate-spin mb-3" />
        <p className="text-slate-500 text-sm font-medium">Authenticating vault session...</p>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-[#F9FAFB] text-[#111827] flex flex-col items-center justify-center py-12 px-4 sm:px-6">
        {/* BRAND HEADER */}
        <div className="text-center mb-8">
          <span className="text-3xl font-extrabold tracking-tight text-slate-900">FinSight</span>
        </div>

        {/* AUTH FORM CARD */}
        <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          {/* TAB SWITCHER */}
          <div className="grid grid-cols-2 p-1 bg-slate-100 rounded-xl text-xs font-semibold">
            <button
              onClick={() => { setAuthMode("login"); setAuthError(null); }}
              className={`py-2 rounded-lg transition flex items-center justify-center space-x-1.5 cursor-pointer ${
                authMode === "login"
                  ? "bg-white text-slate-900 shadow-xs font-bold"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
            <button
              onClick={() => { setAuthMode("register"); setAuthError(null); }}
              className={`py-2 rounded-lg transition flex items-center justify-center space-x-1.5 cursor-pointer ${
                authMode === "register"
                  ? "bg-white text-slate-900 shadow-xs font-bold"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Create Profile</span>
            </button>
          </div>

          {/* ERROR ALERT */}
          {authError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{authError}</span>
            </div>
          )}

          {/* SIGN IN FORM */}
          {authMode === "login" ? (
            <form onSubmit={(e) => { e.preventDefault(); handleLogin(); }} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Username
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={authLoginForm.username}
                    onChange={(e) => setAuthLoginForm({ ...authLoginForm, username: e.target.value })}
                    placeholder="e.g. azizul or vikram"
                    className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-hidden focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Security PIN
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    value={authLoginForm.pin}
                    onChange={(e) => setAuthLoginForm({ ...authLoginForm, pin: e.target.value })}
                    placeholder="Default: 1234"
                    className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-hidden focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                    required
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Default PIN for all pre-seeded accounts is 1234</p>
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs tracking-wide transition shadow-sm disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
              >
                {authLoading ? (
                  <>
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to Vault</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </form>
          ) : (
            /* REGISTRATION FORM */
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  value={authRegisterForm.name}
                  onChange={(e) => setAuthRegisterForm({ ...authRegisterForm, name: e.target.value })}
                  placeholder="e.g. Rahul Sharma"
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-hidden focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Username (Vault Handle)
                </label>
                <input
                  type="text"
                  value={authRegisterForm.username}
                  onChange={(e) => setAuthRegisterForm({ ...authRegisterForm, username: e.target.value })}
                  placeholder="e.g. rahul"
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-hidden focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Security PIN
                </label>
                <input
                  type="password"
                  value={authRegisterForm.pin}
                  onChange={(e) => setAuthRegisterForm({ ...authRegisterForm, pin: e.target.value })}
                  placeholder="4-digit PIN (default 1234)"
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-hidden focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Email (Optional)
                </label>
                <input
                  type="email"
                  value={authRegisterForm.email}
                  onChange={(e) => setAuthRegisterForm({ ...authRegisterForm, email: e.target.value })}
                  placeholder="e.g. rahul@example.com"
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-hidden focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                />
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs tracking-wide transition shadow-sm disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
              >
                {authLoading ? (
                  <>
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                    <span>Creating Vault...</span>
                  </>
                ) : (
                  <>
                    <span>Create Isolated Vault</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F9FAFB] flex flex-col items-center justify-center p-6">
        <div className="w-8 h-8 rounded-full border-2 border-slate-300 border-t-slate-900 animate-spin mb-3" />
        <p className="text-slate-500 text-sm font-medium">Loading ledger data for {currentUser.name}...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F9FAFB] text-[#111827] flex flex-col w-full">
      {/* CLEAN MINIMALIST NAVBAR - ALIGNED WITH MAX-W-7XL PAGE CONTAINER */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-50 w-full h-14">
        <div className="w-full max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 flex items-center justify-between h-full">
          <div className="flex items-center space-x-4 sm:space-x-8 xl:space-x-10 h-full">
            <div className="flex items-center space-x-2.5 shrink-0">
              {/* Mobile Hamburger Button */}
              {hasStatement ? (
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="lg:hidden w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white hover:bg-slate-800 transition cursor-pointer shadow-xs focus:outline-none"
                  aria-label="Toggle navigation menu"
                >
                  {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
                </button>
              ) : null}

              <span className="text-lg font-extrabold tracking-tight text-slate-900">FinSight</span>
            </div>

            {/* DESKTOP MINIMAL UNDERLINE TABS (KEPT IDENTICAL ON DESKTOP) */}
            {hasStatement && (
              <nav className="hidden lg:flex items-center space-x-6 xl:space-x-8 h-full">
                <button
                  onClick={() => setActiveTab("dashboard")}
                  className={`h-full flex items-center space-x-2 text-sm font-medium border-b-2 transition ${
                    activeTab === "dashboard"
                      ? "border-slate-900 text-slate-900 font-semibold"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span>Overview</span>
                </button>

                <button
                  onClick={() => setActiveTab("spend")}
                  className={`h-full flex items-center space-x-2 text-sm font-medium border-b-2 transition ${
                    activeTab === "spend"
                      ? "border-slate-900 text-slate-900 font-semibold"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <Calendar className="w-4 h-4" />
                  <span>Monthly Drilldown</span>
                </button>

                <button
                  onClick={() => setActiveTab("goals")}
                  className={`h-full flex items-center space-x-2 text-sm font-medium border-b-2 transition ${
                    activeTab === "goals"
                      ? "border-slate-900 text-slate-900 font-semibold"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <Target className="w-4 h-4" />
                  <span>Goal Simulator</span>
                </button>

                <button
                  onClick={() => setActiveTab("insurance")}
                  className={`h-full flex items-center space-x-2 text-sm font-medium border-b-2 transition ${
                    activeTab === "insurance"
                      ? "border-slate-900 text-slate-900 font-semibold"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <ShieldAlert className="w-4 h-4" />
                  <span>Insurance Planner</span>
                </button>

                <button
                  onClick={() => setActiveTab("statements")}
                  className={`h-full flex items-center space-x-2 text-sm font-medium border-b-2 transition ${
                    activeTab === "statements"
                      ? "border-slate-900 text-slate-900 font-semibold"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  <span>Statements</span>
                </button>

                <button
                  onClick={() => setActiveTab("merchants")}
                  className={`h-full flex items-center space-x-2 text-sm font-medium border-b-2 transition ${
                    activeTab === "merchants"
                      ? "border-slate-900 text-slate-900 font-semibold"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <Sparkles className="w-4 h-4 text-amber-500" />
                  <span>Merchant Intel.</span>
                  {merchantStats.pending_review > 0 && (
                    <span className="px-1.5 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 rounded-full border border-amber-300">
                      {merchantStats.pending_review}
                    </span>
                  )}
                </button>

                <button
                  onClick={() => setActiveTab("finneas")}
                  className={`h-full flex items-center space-x-2 text-sm font-medium border-b-2 transition ${
                    activeTab === "finneas"
                      ? "border-purple-600 text-purple-900 font-semibold"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <span className="font-bold bg-gradient-to-r from-purple-700 to-indigo-700 bg-clip-text text-transparent">
                    Finneas
                  </span>
                  <span className="px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-800 text-[10px] font-bold">
                    AI
                  </span>
                </button>
              </nav>
            )}
          </div>

          {/* RIGHT METADATA & PROFILE BUTTONS */}
          <div className="flex items-center space-x-3">
            {currentUser && (
              <div className="relative pl-2" ref={profileMenuRef}>
                <button
                  onClick={() => setShowProfileMenu((prev) => !prev)}
                  title={`${currentUser.name} (${currentUser.is_persona ? "Persona Profile" : "Personal Vault"})`}
                  className="w-8 h-8 rounded-full p-[2px] bg-gradient-to-tr from-blue-600 via-indigo-500 to-sky-400 hover:scale-105 transition-transform duration-150 relative flex items-center justify-center cursor-pointer shadow-xs focus:outline-hidden"
                >
                  <div className="w-full h-full rounded-full bg-slate-900 text-white flex items-center justify-center text-[11px] font-bold tracking-tight">
                    {currentUser.avatar_initials || "U"}
                  </div>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 border-2 border-white absolute bottom-0 right-0 shadow-xs" />
                </button>

                {/* DROPDOWN POPOVER */}
                {showProfileMenu && (
                  <div className="absolute right-0 top-11 w-64 bg-white rounded-xl border border-slate-200 shadow-xl py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
                    {/* User Info Header */}
                    <div className="px-4 py-3 border-b border-slate-100 flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full p-[2px] bg-gradient-to-tr from-blue-600 via-indigo-500 to-sky-400 flex items-center justify-center shrink-0 shadow-xs">
                        <div className="w-full h-full rounded-full bg-slate-900 text-white flex items-center justify-center text-xs font-bold">
                          {currentUser.avatar_initials || "U"}
                        </div>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-bold text-slate-900 truncate">
                          {currentUser.name}
                        </div>
                        <div className="text-[11px] text-slate-400 font-medium truncate">
                          @{currentUser.username}
                        </div>
                        <div className="mt-1">
                          <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            currentUser.is_persona
                              ? "bg-amber-100 text-amber-800 border border-amber-200"
                              : "bg-blue-100 text-blue-800 border border-blue-200"
                          }`}>
                            {currentUser.is_persona ? "Persona Profile" : "Personal Vault"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Profile Tagline / Meta */}
                    {currentUser.tagline && (
                      <div className="px-4 py-2 text-[11px] text-slate-500 leading-relaxed border-b border-slate-100 bg-slate-50/50">
                        {currentUser.tagline}
                      </div>
                    )}

                    {/* Sign Out Action */}
                    <div className="pt-1">
                      <button
                        onClick={() => {
                          setShowProfileMenu(false);
                          handleSignOut();
                        }}
                        className="w-full px-4 py-2.5 text-left text-xs font-semibold text-rose-600 hover:bg-rose-50 flex items-center space-x-2 transition cursor-pointer"
                      >
                        <LogOut className="w-3.5 h-3.5 text-rose-500" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* MOBILE FULL-PAGE DRAWER MENU (Toggled by clicking the Hamburger button) */}
      {hasStatement && mobileMenuOpen && (
        <div className="lg:hidden border-b border-slate-200 bg-white shadow-xl sticky top-14 z-50 animate-in slide-in-from-top-2 duration-150">
          <div className="px-4 py-3 space-y-1">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3 pb-1">
              Select Page
            </div>

            <button
              onClick={() => {
                setActiveTab("dashboard");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                activeTab === "dashboard"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <LayoutDashboard className={`w-4 h-4 ${activeTab === "dashboard" ? "text-white" : "text-slate-500"}`} />
                <span>Overview</span>
              </div>
              {activeTab === "dashboard" && <Check className="w-3.5 h-3.5 text-white" />}
            </button>

            <button
              onClick={() => {
                setActiveTab("spend");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                activeTab === "spend"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Calendar className={`w-4 h-4 ${activeTab === "spend" ? "text-white" : "text-slate-500"}`} />
                <span>Monthly Drilldown</span>
              </div>
              {activeTab === "spend" && <Check className="w-3.5 h-3.5 text-white" />}
            </button>

            <button
              onClick={() => {
                setActiveTab("goals");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                activeTab === "goals"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Target className={`w-4 h-4 ${activeTab === "goals" ? "text-white" : "text-slate-500"}`} />
                <span>Goal Simulator</span>
              </div>
              {activeTab === "goals" && <Check className="w-3.5 h-3.5 text-white" />}
            </button>

            <button
              onClick={() => {
                setActiveTab("insurance");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                activeTab === "insurance"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <ShieldAlert className={`w-4 h-4 ${activeTab === "insurance" ? "text-white" : "text-slate-500"}`} />
                <span>Insurance Planner</span>
              </div>
              {activeTab === "insurance" && <Check className="w-3.5 h-3.5 text-white" />}
            </button>

            <button
              onClick={() => {
                setActiveTab("statements");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                activeTab === "statements"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <FileText className={`w-4 h-4 ${activeTab === "statements" ? "text-white" : "text-slate-500"}`} />
                <span>Statements</span>
              </div>
              {activeTab === "statements" && <Check className="w-3.5 h-3.5 text-white" />}
            </button>

            <button
              onClick={() => {
                setActiveTab("merchants");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                activeTab === "merchants"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Sparkles className={`w-4 h-4 ${activeTab === "merchants" ? "text-amber-400" : "text-amber-500"}`} />
                <span>Merchant Intel.</span>
              </div>
              {merchantStats.pending_review > 0 ? (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                  {merchantStats.pending_review} to review
                </span>
              ) : activeTab === "merchants" ? (
                <Check className="w-3.5 h-3.5 text-white" />
              ) : null}
            </button>

            <button
              onClick={() => {
                setActiveTab("finneas");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                activeTab === "finneas"
                  ? "bg-purple-600 text-white shadow-xs"
                  : "text-purple-700 bg-purple-50 hover:bg-purple-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Sparkles className={`w-4 h-4 ${activeTab === "finneas" ? "text-white" : "text-purple-600"}`} />
                <span>Finneas AI Assistant</span>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${activeTab === "finneas" ? "bg-white/20 text-white" : "bg-purple-200 text-purple-900"}`}>
                Chat
              </span>
            </button>
          </div>
        </div>
      )}

      {/* MOBILE HORIZONTAL QUICK SCROLL TABS BAR (< lg) */}
      {hasStatement && (
        <div className="lg:hidden flex items-center space-x-1.5 px-3 py-2 border-b border-slate-200 bg-white overflow-x-auto no-scrollbar scroll-smooth sticky top-14 z-30">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition shrink-0 ${
              activeTab === "dashboard"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Overview</span>
          </button>

          <button
            onClick={() => setActiveTab("spend")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition shrink-0 ${
              activeTab === "spend"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>Monthly</span>
          </button>

          <button
            onClick={() => setActiveTab("goals")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition shrink-0 ${
              activeTab === "goals"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            <span>Goals</span>
          </button>

          <button
            onClick={() => setActiveTab("insurance")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition shrink-0 ${
              activeTab === "insurance"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Insurance</span>
          </button>

          <button
            onClick={() => setActiveTab("statements")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition shrink-0 ${
              activeTab === "statements"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Statements</span>
          </button>

          <button
            onClick={() => setActiveTab("merchants")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition shrink-0 ${
              activeTab === "merchants"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>Merchant Intel.</span>
            {merchantStats.pending_review > 0 && (
              <span className="px-1.5 py-0.2 text-[9px] font-bold bg-amber-200 text-amber-900 rounded-full">
                {merchantStats.pending_review}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("finneas")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition shrink-0 ${
              activeTab === "finneas"
                ? "bg-purple-600 text-white shadow-xs"
                : "bg-purple-50 text-purple-700 hover:bg-purple-100"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Finneas</span>
          </button>
        </div>
      )}

      {uploadStatus && (
        <div className="bg-blue-50 border-b border-blue-100 text-blue-700 px-4 sm:px-8 py-2 text-xs font-medium flex items-center space-x-2">
          <Activity className="w-3.5 h-3.5 animate-pulse" />
          <span>{uploadStatus}</span>
        </div>
      )}

      {/* INTELLIGENT MERCHANT REVIEW BANNER */}
      {hasStatement && merchantStats.pending_review > 0 && showReviewBanner && activeTab !== "merchants" && (
        <div className="bg-amber-50/90 border-b border-amber-200 px-4 sm:px-8 py-2.5 flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between text-xs text-amber-900 shadow-xs">
          <div className="flex items-center space-x-2.5">
            <Sparkles className="w-4 h-4 text-amber-600 animate-pulse shrink-0" />
            <span>
              <strong>Merchant Intelligence:</strong> Gemini classified {merchantStats.total} merchants.{" "}
              <span className="font-semibold text-amber-800 underline decoration-amber-400">
                {merchantStats.pending_review} items
              </span>{" "}
              have low confidence and need your review.
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                setActiveTab("merchants");
                setMerchantFilter("pending");
              }}
              className="px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-700 text-white font-semibold transition text-xs shadow-xs cursor-pointer"
            >
              Review Now
            </button>
            <button
              onClick={() => setShowReviewBanner(false)}
              className="text-amber-500 hover:text-amber-800 text-sm font-bold cursor-pointer"
              title="Dismiss"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* ZERO-STATE SCREEN: NO STATEMENT LOADED                    */}
      {/* ========================================================= */}
      {!hasStatement ? (
        <main className="w-full max-w-3xl mx-auto px-6 pt-10 pb-16 flex flex-col items-center space-y-6">
          <div className="text-center space-y-1.5">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Upload Your Bank Statement
            </h2>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Drop your last year's PDF or CSV statement. All expense categories, recurring charges, insurance gaps, and goals will be parsed locally.
            </p>
          </div>

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`w-full p-10 rounded-2xl bg-white border-2 border-dashed transition flex flex-col items-center justify-center text-center space-y-4 shadow-sm ${
              isDragging
                ? "border-slate-900 bg-slate-50 ring-4 ring-slate-900/5"
                : "border-slate-300 hover:border-slate-400"
            }`}
          >
            <div className="p-3 rounded-xl bg-slate-100 text-slate-700">
              <FileCheck2 className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-900">
                Drag & drop your bank statement(s) here
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <label className="px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold cursor-pointer transition shadow-sm">
                <span>{uploading ? "Analyzing Document(s)..." : "Browse Statement Files"}</span>
                <input
                  type="file"
                  accept=".pdf,.csv,.xlsx,.xls"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={uploading}
                />
              </label>
            </div>
          </div>
        </main>
      ) : (
        /* ========================================================= */
        /* FULL-WIDTH DASHBOARD SCREENS                              */
        /* ========================================================= */
        <div className="w-full max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-4 sm:space-y-6 overflow-x-hidden min-w-0">
          {/* TAB 1: OVERVIEW */}
          {activeTab === "dashboard" && (
            <div className="space-y-4 sm:space-y-6 min-w-0">
              {/* ROW 1: PRIMARY KPI RIBBON (FULL WIDTH) */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-4 min-w-0">
                {/* Total Inflow */}
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div className="flex justify-between items-start">
                    <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Annual Inflow
                    </span>
                    <ArrowUpRight className="w-4 h-4 text-emerald-600 shrink-0" />
                  </div>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight truncate block">
                      ₹{Number(overview?.total_inflow || 0).toLocaleString()}
                    </span>
                  </div>
                  <span className="text-[11px] sm:text-xs font-medium text-emerald-700 truncate">Salary + Annual Bonus</span>
                </div>

                {/* Total Outflow */}
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div className="flex justify-between items-start">
                    <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Annual Burn
                    </span>
                    <ArrowDownRight className="w-4 h-4 text-rose-600 shrink-0" />
                  </div>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight truncate block">
                      ₹{Number(overview?.total_outflow || 0).toLocaleString()}
                    </span>
                  </div>
                  <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">
                    {overview?.transactions_count || 0} Transactions
                  </span>
                </div>

                {/* Savings Rate */}
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div className="flex justify-between items-start">
                    <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Savings Rate
                    </span>
                    <TrendingUp className="w-4 h-4 text-amber-600 shrink-0" />
                  </div>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight truncate block">
                      {overview?.savings_rate ?? 0}%
                    </span>
                  </div>
                  <span className="text-[11px] sm:text-xs font-medium text-amber-700 truncate">Target: 20%+</span>
                </div>

                {/* Liquid Balance */}
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div className="flex justify-between items-start">
                    <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Liquid Buffer
                    </span>
                    <Wallet className="w-4 h-4 text-slate-500 shrink-0" />
                  </div>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight truncate block">
                      ₹{Number(overview?.end_balance ?? overview?.net_savings ?? 0).toLocaleString()}
                    </span>
                  </div>
                  <span className={`text-[11px] sm:text-xs font-medium truncate ${(overview?.end_balance ?? 0) >= 0 ? "text-slate-500" : "text-rose-600"}`}>
                    {(overview?.end_balance ?? 0) >= 0
                      ? `~${Math.max(0, Math.round(((overview?.end_balance || 0) / Math.max(1, (overview?.total_outflow || 1) / 12)) * 10) / 10)} Mo Runway`
                      : "Deficit (Depleted Runway)"}
                  </span>
                </div>
              </div>

              {/* ROW 2: CHARTS (FULL-WIDTH 70/30 GRID) */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 min-w-0">
                {/* 12-Month Inflow vs Outflow */}
                <div className="lg:col-span-2 p-4 sm:p-6 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between min-w-0 overflow-hidden">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h2 className="text-base font-bold text-slate-900">Inflow vs Burn Rate</h2>
                        <p className="text-xs text-slate-500">Monthly Cash Inflow vs Outflow</p>
                      </div>
                      <div className="flex items-center space-x-4 text-xs font-medium">
                        <div className="flex items-center space-x-1.5 text-slate-700">
                          <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
                          <span>Inflow</span>
                        </div>
                        <div className="flex items-center space-x-1.5 text-slate-700">
                          <span className="w-2.5 h-2.5 rounded-sm bg-blue-600" />
                          <span>Burn</span>
                        </div>
                      </div>
                    </div>

                    <div className="h-68 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={overview?.monthly_metrics || overview?.monthly_trend || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <XAxis dataKey="year_month" stroke="#94A3B8" fontSize={11} tickLine={false} />
                          <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} tickFormatter={(v) => `₹${v / 1000}k`} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#FFFFFF",
                              borderColor: "#E2E8F0",
                              borderRadius: "8px",
                              fontSize: "12px",
                              boxShadow: "0 4px 6px -1px rgba(0,0,0,0.08)",
                            }}
                            formatter={(val: any, name: any) => [`₹${Number(val).toLocaleString()}`, name === "income" ? "Inflow" : name === "expenses" ? "Burn" : name]}
                          />
                          <Bar dataKey="income" name="Inflow" fill="#059669" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="expenses" name="Burn" fill="#2563EB" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Spending Breakdown Donut (COMPACT LEGEND, ZERO OVERFLOW) */}
                <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <h2 className="text-base font-bold text-slate-900">Spending Breakdown</h2>
                      <div className="flex items-center p-0.5 rounded-md bg-slate-100 border border-slate-200 text-xs">
                        <button
                          onClick={() => setBreakdownView("granular")}
                          className={`px-2 py-0.5 rounded font-medium transition ${
                            breakdownView === "granular"
                              ? "bg-white text-slate-900 shadow-xs"
                              : "text-slate-500 hover:text-slate-900"
                          }`}
                        >
                          Granular
                        </button>
                        <button
                          onClick={() => setBreakdownView("macro")}
                          className={`px-2 py-0.5 rounded font-medium transition ${
                            breakdownView === "macro"
                              ? "bg-white text-slate-900 shadow-xs"
                              : "text-slate-500 hover:text-slate-900"
                          }`}
                        >
                          Macro
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 mb-2">Annual spending allocation</p>

                    <div className="h-48 w-full flex items-center justify-center">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={
                              breakdownView === "granular"
                                ? overview.subcategory_breakdown || overview.category_breakdown
                                : overview.category_breakdown
                            }
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={75}
                            paddingAngle={3}
                            dataKey="value"
                          >
                            {(breakdownView === "granular"
                              ? overview.subcategory_breakdown || overview.category_breakdown
                              : overview.category_breakdown
                            ).map((_: any, index: number) => (
                              <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#FFFFFF",
                              borderColor: "#E2E8F0",
                              borderRadius: "8px",
                              fontSize: "12px",
                              boxShadow: "0 4px 6px -1px rgba(0,0,0,0.08)",
                            }}
                            formatter={(v: any) => [`₹${Number(v).toLocaleString()}`, "Spend"]}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-2 pt-2 border-t border-slate-100 text-xs">
                    {(breakdownView === "granular"
                      ? overview.subcategory_breakdown || overview.category_breakdown
                      : overview.category_breakdown
                    ).map((c: any, i: number) => (
                      <div key={i} className="flex items-center space-x-1.5 truncate">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }}
                        />
                        <span className="truncate text-slate-600" title={c.name}>
                          {c.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* ROW 3: AI STRATEGIC FINANCIAL & PATTERN AUDIT */}
              <div className="rounded-xl bg-white border border-slate-200 p-6 space-y-5 shadow-xs">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between pb-4 border-b border-slate-100 gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                      <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0 text-indigo-600">
                        <Sparkles className="w-4 h-4" />
                      </div>
                      <h2 className="text-base font-bold text-slate-900">
                        AI Strategic Multi-Month Audit
                      </h2>
                      <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                        {subscriptions?.period || "Full Statement History"}
                      </span>
                    </div>
                    {subscriptions?.executive_headline && (
                      <h3 className="text-sm font-bold text-slate-900 pt-1">
                        {renderHighlightedText(subscriptions.executive_headline)}
                      </h3>
                    )}
                    {subscriptions?.macro_summary && (
                      <p className="text-xs text-slate-600 leading-relaxed pt-0.5">
                        {renderHighlightedText(subscriptions.macro_summary)}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={handleRefreshAudit}
                    disabled={isRefreshingAudit}
                    className="self-end sm:self-auto px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 text-xs font-medium flex items-center space-x-1.5 transition shrink-0 disabled:opacity-50 cursor-pointer"
                  >
                    <RefreshCcw className={`w-3.5 h-3.5 ${isRefreshingAudit ? "animate-spin" : ""}`} />
                    <span>{isRefreshingAudit ? "Analyzing..." : "Re-Analyze"}</span>
                  </button>
                </div>

                {/* Sub-Section 1: Recurring Commitments & Fixed Debt */}
                {subscriptions?.recurring_commitments && subscriptions.recurring_commitments.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Recurring Commitments & Fixed Debt
                    </h4>

                    <div className="divide-y divide-slate-100">
                      {subscriptions.recurring_commitments.map((rec: any, idx: number) => {
                        const sev = rec.severity || "info";
                        const pillClass =
                          sev === "danger"
                            ? "bg-rose-50 text-rose-700 border-rose-200"
                            : sev === "warning"
                            ? "bg-amber-50 text-amber-700 border-amber-200"
                            : "bg-blue-50 text-blue-700 border-blue-200";

                        return (
                          <div
                            key={idx}
                            className="py-3.5 first:pt-1 last:pb-1 flex flex-col sm:flex-row sm:items-start justify-between gap-3 sm:gap-4"
                          >
                            <div className="sm:w-52 shrink-0 pt-0.5">
                              <span className={`inline-block text-[11px] font-semibold px-2.5 py-0.5 rounded border ${pillClass}`}>
                                {stripMarkdown(rec.type_label)}
                              </span>
                            </div>

                            <div className="flex-1 space-y-0.5 min-w-0">
                              <h5 className="text-sm font-bold text-slate-900">
                                {stripMarkdown(rec.entity)}
                              </h5>
                              <p className="text-xs text-slate-600 leading-relaxed">
                                {renderHighlightedText(rec.cadence_detail)}
                              </p>
                            </div>

                            <div className="sm:text-right shrink-0 sm:pl-4 pt-0.5">
                              <span className="block text-[11px] text-slate-400 font-medium">Monthly Run-Rate</span>
                              <span className="text-sm font-bold text-slate-900">
                                {stripMarkdown(rec.monthly_runrate)}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Sub-Section 2: Behavioral Signatures */}
                {subscriptions?.behavioral_patterns && subscriptions.behavioral_patterns.length > 0 && (
                  <div className="space-y-2.5 pt-3 border-t border-slate-100">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 pb-1">
                      Behavioral Signatures
                    </h4>

                    <div className="space-y-2.5">
                      {subscriptions.behavioral_patterns.map((pat: any, idx: number) => (
                        <div key={idx} className="flex items-start space-x-2.5">
                          <span className="text-slate-400 font-bold mt-0.5 select-none text-sm leading-none">•</span>
                          <p className="text-xs text-slate-600 leading-relaxed">
                            <strong className="font-bold text-slate-900 mr-1.5">
                              {stripMarkdown(pat.title)}:
                            </strong>
                            {renderHighlightedText(pat.detail)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Sub-Section 3: Strategic Portfolio Directive */}
                {subscriptions?.strategic_recommendation && (
                  <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-amber-950 flex items-start space-x-3">
                    <Zap className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div className="text-xs leading-relaxed">
                      <span className="font-bold text-amber-900 mr-1.5">
                        Strategic Portfolio Directive:
                      </span>
                      <span className="text-amber-900/90">
                        {renderHighlightedText(subscriptions.strategic_recommendation)}
                      </span>
                    </div>
                  </div>
                )}

                {/* Legacy Fallback if neither recurring_commitments nor behavioral_patterns present */}
                {(!subscriptions?.recurring_commitments && !subscriptions?.behavioral_patterns) && (
                  subscriptions?.items && subscriptions.items.length > 0 ? (
                    <div className="divide-y divide-slate-100">
                      {subscriptions.items.map((item: any, idx: number) => (
                        <div
                          key={idx}
                          className="py-3.5 first:pt-1 last:pb-1 flex flex-col sm:flex-row sm:items-start justify-between gap-3 sm:gap-4"
                        >
                          <div className="sm:w-52 shrink-0 pt-0.5">
                            <span className="inline-block text-[11px] font-semibold px-2.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                              {stripMarkdown(item.badge)}
                            </span>
                          </div>
                          <div className="flex-1 space-y-0.5 min-w-0">
                            <h5 className="text-sm font-bold text-slate-900">{stripMarkdown(item.title)}</h5>
                            <p className="text-xs text-slate-600 leading-relaxed">{renderHighlightedText(item.details)}</p>
                          </div>
                          <div className="sm:text-right shrink-0 sm:pl-4 pt-0.5">
                            <span className="block text-[11px] text-slate-400 font-medium">{item.metric_label}</span>
                            <span className="text-sm font-bold text-slate-900">
                              {stripMarkdown(item.metric_value)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
                      No multi-month statements loaded yet to perform strategic audit.
                    </div>
                  )
                )}
              </div>

              {/* ROW 4: INSURANCE GAP AUDIT */}
              <div className="rounded-xl bg-white border border-slate-200 p-6 space-y-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <ShieldAlert className="w-4 h-4 text-rose-600" />
                    <h2 className="text-base font-bold text-slate-900">Insurance Protection & Gap Analysis</h2>
                  </div>
                  <span
                    className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                      insurance?.life_insurance?.status === "CRITICAL GAP" || !insurance?.health_insurance?.has_policy
                        ? "bg-rose-50 text-rose-700 border-rose-200"
                        : "bg-emerald-50 text-emerald-700 border-emerald-200"
                    }`}
                  >
                    {insurance?.life_insurance?.status === "CRITICAL GAP" || !insurance?.health_insurance?.has_policy
                      ? "Critical Gap"
                      : "Adequately Protected"}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs font-semibold text-slate-700">Life Insurance Cover</span>
                      <span className="text-xs font-bold text-rose-600">
                        {insurance?.life_insurance
                          ? `₹${(insurance.life_insurance.coverage_gap / 10000000).toFixed(2)} Crore Shortfall`
                          : "Evaluating..."}
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden flex">
                      <div
                        className="bg-emerald-500 h-full"
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(
                              3,
                              ((insurance?.life_insurance?.detected_cover || 0) /
                                (insurance?.life_insurance?.recommended_cover || 1)) *
                                100
                            )
                          )}%`,
                        }}
                        title={`Detected: ₹${((insurance?.life_insurance?.detected_cover || 0) / 100000).toFixed(1)}L`}
                      />
                      <div className="bg-rose-500 h-full flex-1" />
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {insurance?.life_insurance?.insight}
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs font-semibold text-slate-700">Health Insurance Cover</span>
                      <span
                        className={`text-xs font-bold ${
                          insurance?.health_insurance?.has_policy ? "text-emerald-600" : "text-rose-600"
                        }`}
                      >
                        {insurance?.health_insurance?.has_policy ? "Active Policy Detected" : "Zero Policy Debits Found"}
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                      <div
                        className={`h-full w-full ${
                          insurance?.health_insurance?.has_policy ? "bg-emerald-500" : "bg-rose-500"
                        }`}
                      />
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {insurance?.health_insurance?.insight}
                    </p>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <p className="text-xs text-slate-500">
                    Audit Human Life Value (HLV) deficit, health protection, and pure term vs endowment comparisons.
                  </p>
                  <button
                    onClick={() => setActiveTab("insurance")}
                    className="inline-flex items-center justify-center space-x-1.5 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition shadow-xs shrink-0 cursor-pointer"
                  >
                    <span>Open Insurance Planner</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}


          {activeTab === "goals" && (
            <div className="space-y-6">
              {/* HEADER */}
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 truncate">
                    Goal Planner
                  </h2>
                </div>
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => setShowCreateGoalModal(true)}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-xs transition cursor-pointer shrink-0"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create New Goal</span>
                  </button>
                </div>
              </div>

              {/* 1. CASHFLOW REALITY STRIP (Clean 4-card Ribbon) */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-4 min-w-0">
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">Statement Inflow</span>
                    <TrendingUp className="w-4 h-4 text-emerald-600 shrink-0" />
                  </div>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight truncate block">
                      ₹{Number(cashflowContext?.avg_monthly_income || 0).toLocaleString()}
                    </span>
                  </div>
                  <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">Average monthly deposits</span>
                </div>

                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">Mandatory Burn</span>
                    <Flame className="w-4 h-4 text-rose-500 shrink-0" />
                  </div>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-rose-600 tracking-tight truncate block">
                      ₹{Number(cashflowContext?.mandatory_monthly_burn || 0).toLocaleString()}
                    </span>
                  </div>
                  <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">Fixed essentials, EMIs & utilities</span>
                </div>

                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                      {Number(cashflowContext?.net_monthly_cashflow ?? (cashflowContext?.avg_monthly_surplus || 0)) >= 0 ? "Monthly Surplus" : "Cashflow Deficit"}
                    </span>
                    <Wallet className={`w-4 h-4 shrink-0 ${Number(cashflowContext?.net_monthly_cashflow ?? 0) >= 0 ? "text-emerald-500" : "text-rose-500"}`} />
                  </div>
                  <div className="my-1.5 sm:my-2">
                    <span className={`text-xl sm:text-2xl lg:text-3xl font-extrabold tracking-tight truncate block ${Number(cashflowContext?.net_monthly_cashflow ?? 0) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                      {Number(cashflowContext?.net_monthly_cashflow ?? 0) >= 0 ? "+" : "-"}₹{Math.abs(Number(cashflowContext?.net_monthly_cashflow ?? (cashflowContext?.avg_monthly_surplus || 0))).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                  <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">
                    {Number(cashflowContext?.net_monthly_cashflow ?? 0) >= 0 ? "Net surplus generated" : "Current expenses exceed inflow"}
                  </span>
                </div>

                {/* 4. Remaining Surplus (Available to Allocate) */}
                {(() => {
                  const baseSurplus = Number(cashflowContext?.avg_monthly_surplus || 0);
                  const allocatedToGoals = goalsList.reduce((acc, g) => acc + Number(g.monthly_allocation || 0), 0);
                  const remainingSurplus = baseSurplus - allocatedToGoals;
                  const isPositive = remainingSurplus >= 0;

                  return (
                    <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                          {isPositive ? "Remaining Surplus" : "Surplus Deficit"}
                        </span>
                        <PiggyBank className={`w-4 h-4 shrink-0 ${isPositive ? "text-emerald-500" : "text-amber-500"}`} />
                      </div>
                      <div className="my-1.5 sm:my-2">
                        <span className={`text-xl sm:text-2xl lg:text-3xl font-extrabold tracking-tight truncate block ${isPositive ? "text-emerald-600" : "text-amber-600"}`}>
                          {isPositive ? "+" : "-"}₹{Math.abs(remainingSurplus).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">
                        {isPositive
                          ? `Available after ${goalsList.length} goal${goalsList.length === 1 ? "" : "s"}`
                          : `Exceeds surplus by ₹${Math.abs(remainingSurplus).toLocaleString()}/mo`}
                      </span>
                    </div>
                  );
                })()}
              </div>

              {/* 2. SAVED GOAL PORTFOLIO (Shown only when active goals exist) */}
              {goalsList.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Target className="w-4 h-4 text-slate-900" />
                      <h3 className="text-sm font-bold text-slate-900">Your Saved Goals</h3>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold">
                        {goalsList.length} Active
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {goalsList.map((g: any) => {
                      const isActive = g.id === activeGoalId;
                      return (
                        <div
                          key={g.id}
                          onClick={() => handleSelectGoal(g)}
                          className={`p-4 rounded-xl border text-xs transition cursor-pointer relative group ${
                            isActive
                              ? "bg-blue-50/50 border-blue-500 shadow-sm ring-1 ring-blue-500"
                              : "bg-white border-slate-200 hover:border-slate-300 shadow-2xs"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center space-x-2.5">
                              <div
                                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                                  g.category === "EMERGENCY"
                                    ? "bg-emerald-100 text-emerald-700"
                                    : g.category === "VACATION"
                                    ? "bg-blue-100 text-blue-700"
                                    : g.category === "ASSET"
                                    ? "bg-purple-100 text-purple-700"
                                    : "bg-slate-100 text-slate-700"
                                }`}
                              >
                                {g.category === "EMERGENCY" ? (
                                  <Shield className="w-4 h-4" />
                                ) : g.category === "VACATION" ? (
                                  <Plane className="w-4 h-4" />
                                ) : g.category === "ASSET" ? (
                                  <Car className="w-4 h-4" />
                                ) : (
                                  <PiggyBank className="w-4 h-4" />
                                )}
                              </div>
                              <div>
                                <h4 className="font-bold text-slate-900 leading-tight">{g.title}</h4>
                                <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                                  {g.category}
                                </span>
                              </div>
                            </div>

                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteGoal(g.id);
                              }}
                              className="text-slate-300 hover:text-rose-600 transition p-1 cursor-pointer"
                              title="Delete goal"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          <div className="grid grid-cols-2 gap-2 mt-3 pt-2 border-t border-slate-100 text-[11px]">
                            <div>
                              <span className="text-[10px] text-slate-400 block font-medium">TARGET</span>
                              <span className="font-bold text-slate-900">₹{Number(g.target_amount).toLocaleString()}</span>
                            </div>
                            <div>
                              <span className="text-[10px] text-slate-400 block font-medium">MONTHLY SIP</span>
                              <span className="font-bold text-blue-600">
                                ₹{Number(g.monthly_allocation).toLocaleString()}/mo
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 3. SIMULATION CONTROLS & VERDICT GRID */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* LEFT: INTERACTIVE LEVERS (7 COLS) */}
                <div className="lg:col-span-7 rounded-2xl bg-white border border-slate-200/90 p-6 space-y-6 shadow-sm">
                  {/* Card Header */}
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                        <Sliders className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 leading-tight">Interactive Scenario Levers</h3>
                        <p className="text-[11px] text-slate-500">Fine-tune milestone targets, monthly contributions, and discretionary spend cuts</p>
                      </div>
                    </div>
                    <span className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-medium">
                      Live Simulation
                    </span>
                  </div>

                  {/* LEVER 1: TARGET AMOUNT */}
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="text-xs font-bold text-slate-800">Goal Target Amount</span>
                        <span className="text-[11px] text-slate-400 block">Total milestone capital to accumulate</span>
                      </div>
                      <div className="flex items-center bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus-within:border-blue-500 focus-within:bg-white transition shadow-2xs">
                        <span className="text-xs font-semibold text-slate-400 mr-1.5">₹</span>
                        <input
                          type="number"
                          value={simTargetAmount}
                          onChange={(e) => setSimTargetAmount(Math.max(10000, Number(e.target.value)))}
                          className="w-28 text-right font-bold text-slate-900 bg-transparent text-sm focus:outline-none"
                        />
                      </div>
                    </div>
                    <input
                      type="range"
                      min="20000"
                      max="2500000"
                      step="10000"
                      value={simTargetAmount}
                      onChange={(e) => setSimTargetAmount(Number(e.target.value))}
                      className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-100 rounded-lg"
                    />
                    <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                      <span className="text-[10px] uppercase font-bold text-slate-400 mr-1">Presets:</span>
                      {[
                        { label: "₹50k", val: 50000 },
                        { label: "₹1 Lakh", val: 100000 },
                        { label: "₹2.5 Lakh", val: 250000 },
                        { label: "₹5 Lakh", val: 500000 },
                        { label: "₹10 Lakh", val: 1000000 },
                        { label: "₹20 Lakh", val: 2000000 },
                      ].map((preset) => {
                        const isSelected = simTargetAmount === preset.val;
                        return (
                          <button
                            key={preset.val}
                            onClick={() => setSimTargetAmount(preset.val)}
                            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition border cursor-pointer ${
                              isSelected
                                ? "bg-blue-600 text-white border-blue-600 shadow-2xs"
                                : "bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200"
                            }`}
                          >
                            {preset.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* LEVER 2: MONTHLY CONTRIBUTION PACE */}
                  <div className="space-y-3 pt-3 border-t border-slate-100">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-slate-800">Monthly Contribution Pace</span>
                          {/* Dynamic Feasibility Badge */}
                          {(() => {
                            const surplus = Number(cashflowContext?.avg_monthly_surplus || 0);
                            const unlockedCuts = Object.values(simDiscretionaryCuts).reduce((a, b) => a + b, 0);
                            if (surplus > 0 && simMonthlyAllocation <= surplus) {
                              return (
                                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                                  Supported by surplus
                                </span>
                              );
                            } else if (simMonthlyAllocation <= surplus + unlockedCuts && unlockedCuts > 0) {
                              return (
                                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                                  Funded with unlocked cuts
                                </span>
                              );
                            } else {
                              const gap = simMonthlyAllocation - (surplus + unlockedCuts);
                              return (
                                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                                  Requires ₹{gap.toLocaleString()}/mo extra
                                </span>
                              );
                            }
                          })()}
                        </div>
                        <span className="text-[11px] text-slate-400 block mt-0.5">
                          Regular statement cashflow surplus: ₹{Number(cashflowContext?.avg_monthly_surplus || 0).toLocaleString()} / mo
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-base font-bold text-blue-600">
                          ₹{simMonthlyAllocation.toLocaleString()}
                        </span>
                        <span className="text-[10px] text-slate-400 block font-medium">per month</span>
                      </div>
                    </div>
                    <input
                      type="range"
                      min="1000"
                      max="100000"
                      step="1000"
                      value={simMonthlyAllocation}
                      onChange={(e) => setSimMonthlyAllocation(Number(e.target.value))}
                      className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-100 rounded-lg"
                    />

                    <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                      <span className="text-[10px] uppercase font-bold text-slate-400 mr-1">Quick SIP:</span>
                      {[5000, 10000, 15000, 25000, 50000].map((val) => {
                        const isSelected = simMonthlyAllocation === val;
                        return (
                          <button
                            key={val}
                            onClick={() => setSimMonthlyAllocation(val)}
                            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition border cursor-pointer ${
                              isSelected
                                ? "bg-blue-600 text-white border-blue-600 shadow-2xs"
                                : "bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200"
                            }`}
                          >
                            ₹{(val / 1000).toFixed(0)}k
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* LEVER 3: DISCRETIONARY TRIMMING LEVERS (% SLIDERS) */}
                  {cashflowContext?.discretionary_categories && cashflowContext.discretionary_categories.length > 0 && (
                    <div className="space-y-3 pt-3 border-t border-slate-100">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-slate-800">
                              Unlock Cashflow by Trimming Discretionary Spends
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                Object.values(simDiscretionaryCuts).reduce((a, b) => a + b, 0) > 0
                                  ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                                  : "bg-slate-100 text-slate-600"
                              }`}
                            >
                              +₹{Object.values(simDiscretionaryCuts).reduce((a, b) => a + b, 0).toLocaleString()} / mo unlocked
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-400 block mt-0.5">
                            Slide percentage to trim flexible spending and directly fund your goal
                          </span>
                        </div>
                        {Object.values(simDiscretionaryCuts).reduce((a, b) => a + b, 0) > 0 && (
                          <button
                            onClick={() => setSimDiscretionaryCuts({})}
                            className="text-[11px] text-slate-400 hover:text-slate-600 underline font-medium cursor-pointer"
                          >
                            Reset cuts
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {cashflowContext.discretionary_categories.map((cat: any) => {
                          const currentCut = simDiscretionaryCuts[cat.name] || 0;
                          const currentPct = cat.monthly_spend > 0 ? Math.round((currentCut / cat.monthly_spend) * 100) : 0;
                          return (
                            <div
                              key={cat.name}
                              className={`p-3.5 rounded-xl border text-xs space-y-2.5 transition ${
                                currentCut > 0
                                  ? "bg-emerald-50/40 border-emerald-300 ring-1 ring-emerald-300/60"
                                  : "bg-slate-50/70 border-slate-200"
                              }`}
                            >
                              <div className="flex justify-between items-start">
                                <div>
                                  <h5 className="font-bold text-slate-900 text-xs leading-tight">{cat.name}</h5>
                                  <span className="text-[10px] text-slate-400">Spent: ₹{Number(cat.monthly_spend).toLocaleString()}/mo</span>
                                </div>
                                <span
                                  className={`text-xs font-bold ${
                                    currentCut > 0 ? "text-emerald-700" : "text-slate-400"
                                  }`}
                                >
                                  {currentCut > 0 ? `Trim ${currentPct}% (+₹${currentCut.toLocaleString()})` : "0% trim (₹0)"}
                                </span>
                              </div>

                              {/* Percentage Slider: 0% to 50% */}
                              <input
                                type="range"
                                min="0"
                                max="50"
                                step="5"
                                value={currentPct}
                                onChange={(e) => {
                                  const pct = Number(e.target.value);
                                  const cutVal = Math.round((cat.monthly_spend * pct) / 100);
                                  handleCutChange(cat.name, cutVal);
                                }}
                                className="w-full accent-emerald-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
                              />

                              <div className="flex items-center justify-between text-[10px]">
                                <button
                                  type="button"
                                  onClick={() => handleCutChange(cat.name, 0)}
                                  className={`px-2 py-0.5 rounded transition cursor-pointer ${
                                    currentPct === 0
                                      ? "text-slate-800 font-bold bg-white border border-slate-200 shadow-2xs"
                                      : "text-slate-400 hover:text-slate-600"
                                  }`}
                                >
                                  Keep all
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleCutChange(cat.name, Math.round(cat.monthly_spend * 0.15))}
                                  className={`px-2 py-0.5 rounded transition cursor-pointer ${
                                    currentPct === 15
                                      ? "text-emerald-800 font-bold bg-white border border-emerald-200 shadow-2xs"
                                      : "text-slate-400 hover:text-slate-600"
                                  }`}
                                >
                                  Trim 15%
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleCutChange(cat.name, Math.round(cat.monthly_spend * 0.30))}
                                  className={`px-2 py-0.5 rounded transition cursor-pointer ${
                                    currentPct === 30
                                      ? "text-emerald-800 font-bold bg-white border border-emerald-200 shadow-2xs"
                                      : "text-slate-400 hover:text-slate-600"
                                  }`}
                                >
                                  Trim 30%
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleCutChange(cat.name, Math.round(cat.monthly_spend * 0.50))}
                                  className={`px-2 py-0.5 rounded transition cursor-pointer ${
                                    currentPct === 50
                                      ? "text-emerald-800 font-bold bg-white border border-emerald-200 shadow-2xs"
                                      : "text-slate-400 hover:text-slate-600"
                                  }`}
                                >
                                  Max 50%
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* LEVER 4: LUMPSUM SEED & RETURN VEHICLE */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-100 text-xs">
                    {/* Lumpsum Boost */}
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="font-bold text-slate-800 text-xs">Initial Lumpsum Seed</span>
                          <span className="text-[10px] text-slate-400 block">Existing savings or bonus</span>
                        </div>
                        <span className="font-bold text-blue-600 text-xs">
                          ₹{simLumpsum.toLocaleString()}
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="300000"
                        step="5000"
                        value={simLumpsum}
                        onChange={(e) => setSimLumpsum(Number(e.target.value))}
                        className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
                      />
                      <div className="flex flex-wrap gap-1 pt-0.5">
                        {[0, 25000, 50000, 100000].map((val) => (
                          <button
                            key={val}
                            onClick={() => setSimLumpsum(val)}
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold border transition cursor-pointer ${
                              simLumpsum === val
                                ? "bg-blue-600 text-white border-blue-600"
                                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-100"
                            }`}
                          >
                            {val === 0 ? "₹0" : `₹${(val / 1000).toFixed(0)}k`}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Return Vehicle Selection */}
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="font-bold text-slate-800 text-xs">Expected Return Rate</span>
                          <span className="text-[10px] text-slate-400 block">Compounding vehicle CAGR</span>
                        </div>
                        <span className="font-bold text-slate-900 text-xs">{simReturnCagr}% CAGR</span>
                      </div>
                      <div className="grid grid-cols-3 gap-1.5 pt-1">
                        {[
                          { label: "Cash / FD", val: 6.5, desc: "Low risk" },
                          { label: "Hybrid", val: 9.5, desc: "Balanced" },
                          { label: "Equity", val: 12.0, desc: "Growth" },
                        ].map((v) => (
                          <button
                            key={v.val}
                            onClick={() => setSimReturnCagr(v.val)}
                            className={`py-1.5 px-2 rounded-lg text-center border transition cursor-pointer ${
                              simReturnCagr === v.val
                                ? "bg-blue-600 text-white border-blue-600 shadow-2xs"
                                : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
                            }`}
                          >
                            <div className="text-[11px] font-bold leading-tight">{v.label}</div>
                            <div className={`text-[9px] ${simReturnCagr === v.val ? "text-blue-100" : "text-slate-400"}`}>
                              {v.val}% ({v.desc})
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* LEVER 5: INFLATION TOGGLE */}
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        id="inflation-toggle"
                        checked={simInflationRate > 0}
                        onChange={(e) => setSimInflationRate(e.target.checked ? 6.0 : 0.0)}
                        className="rounded accent-blue-600 w-4 h-4 cursor-pointer"
                      />
                      <label htmlFor="inflation-toggle" className="cursor-pointer">
                        <span className="font-bold text-slate-800 block text-xs">
                          Adjust for 6.0% Annual Inflation
                        </span>
                        <span className="text-[11px] text-slate-400 block">
                          Calculates target in real purchasing power so living costs don't erode your savings
                        </span>
                      </label>
                    </div>
                    <span
                      className={`text-[10px] font-semibold px-2.5 py-1 rounded-full shrink-0 ${
                        simInflationRate > 0
                          ? "bg-blue-100 text-blue-800 border border-blue-200"
                          : "bg-slate-200/70 text-slate-600"
                      }`}
                    >
                      {simInflationRate > 0 ? "Inflation Protected" : "Nominal Value"}
                    </span>
                  </div>
                </div>

                {/* RIGHT: EDITORIAL MILESTONE PROJECTION (5 COLS) - PURE WHITE LIGHT MODE! */}
                {simResult && (
                  <div className="lg:col-span-5 rounded-2xl bg-white border border-slate-200 p-6 flex flex-col justify-between space-y-5 shadow-sm">
                    <div className="space-y-5">
                      {/* Milestone Date Hero Card (Soft Gradient, NOT Pitch Black!) */}
                      <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-50/90 via-blue-50/50 to-slate-50 border border-indigo-100 space-y-2">
                        <div className="flex items-center justify-between text-[10px] font-bold tracking-wider uppercase text-slate-500">
                          <span>Projected Completion</span>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            simResult.months_saved > 0
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : "bg-blue-50 text-blue-700 border-blue-200"
                          }`}>
                            {simResult.months_saved > 0 ? `Saves ${simResult.months_saved} months with returns` : "On pace"}
                          </span>
                        </div>
                        <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                          {simResult.target_completion_date}
                        </div>
                        <div className="flex items-baseline space-x-2 text-xs">
                          <span className="font-bold text-indigo-700 text-sm">{simResult.optimized_months} months to target</span>
                          <span className="text-slate-400 text-xs">
                            (Linear baseline: {simResult.baseline_months} mos)
                          </span>
                        </div>
                      </div>

                      {/* Capital Breakdown Decomposition */}
                      <div className="space-y-2 text-xs">
                        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                          Capital Breakdown
                        </div>
                        <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/90 space-y-2.5">
                          <div className="flex justify-between items-center">
                            <span className="text-slate-600">Goal Target Amount:</span>
                            <span className="font-bold text-slate-900">
                              ₹{Number(simResult.target_amount || 0).toLocaleString()}
                            </span>
                          </div>

                          <div className="flex justify-between items-center">
                            <span className="text-slate-600">Principal Out-of-Pocket:</span>
                            <span className="font-bold text-slate-900">
                              ₹{Number(simResult.total_invested || 0).toLocaleString()}
                            </span>
                          </div>

                          <div className="flex justify-between items-center">
                            <span className="text-slate-600">Compounding Wealth Gain:</span>
                            <span className="font-bold text-emerald-600">
                              +₹{Number(simResult.total_interest_earned || 0).toLocaleString()}
                            </span>
                          </div>

                          <div className="flex justify-between items-center pt-2 border-t border-slate-200">
                            <span className="text-slate-600">Discretionary Cuts Unlocked:</span>
                            <span className="font-bold text-emerald-700">
                              +₹{Number(simResult.monthly_cuts_unlocked || 0).toLocaleString()} / mo
                            </span>
                          </div>

                          <div className="flex justify-between items-center">
                            <span className="text-slate-600 font-medium">Effective Monthly Pace:</span>
                            <span className="font-bold text-blue-600">
                              ₹{Number(simResult.optimized_monthly || 0).toLocaleString()} / mo
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Truthful Fiduciary Feasibility Assessment */}
                      <div className={`p-4 rounded-xl border text-xs space-y-1.5 ${
                        simResult.feasibility_status === "fully_funded"
                          ? "bg-emerald-50/80 border-emerald-200 text-emerald-950"
                          : simResult.feasibility_status === "funded_with_cuts"
                          ? "bg-blue-50/80 border-blue-200 text-blue-950"
                          : "bg-amber-50/90 border-amber-200 text-amber-950"
                      }`}>
                        <div className="flex items-center space-x-1.5 font-bold">
                          {simResult.feasibility_status === "deficit" ? (
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                          ) : (
                            <CheckCircle className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                          )}
                          <span>Fiduciary Feasibility Verdict</span>
                        </div>
                        <p className="text-[11px] leading-relaxed">
                          {simResult.feasibility_message || (
                            simResult.feasibility_status === "deficit"
                              ? `Funding gap of ₹${Math.max(0, simMonthlyAllocation - Number(cashflowContext?.avg_monthly_surplus || 0)).toLocaleString()}/month. Requires unlocking further spending cuts or boosting monthly income.`
                              : `Allocating ₹${Number(simResult.optimized_monthly || 0).toLocaleString()}/month is fully supported by your available cashflow.`
                          )}
                        </p>
                      </div>
                    </div>

                    {/* Action: Save this simulation as a tracked goal */}
                    <div className="pt-2">
                      <button
                        onClick={() => {
                          setNewGoalForm({
                            title: "Simulated Goal",
                            category: "SAVINGS",
                            target_amount: simTargetAmount,
                            monthly_allocation: simMonthlyAllocation,
                            lumpsum_infusion: simLumpsum,
                            target_return_cagr: simReturnCagr,
                            description: `Target set at ₹${simTargetAmount.toLocaleString()} with monthly contribution of ₹${simMonthlyAllocation.toLocaleString()}.`,
                          });
                          setShowCreateGoalModal(true);
                        }}
                        className="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs flex items-center justify-center space-x-2 shadow-xs transition cursor-pointer"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Save as Tracked Goal</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>




              {/* 5. CREATE GOAL MODAL */}
              {showCreateGoalModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in">
                  <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
                    <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Target className="w-4 h-4 text-blue-600" />
                        <h3 className="text-sm font-bold text-slate-900">Create New Financial Goal</h3>
                      </div>
                      <button
                        onClick={() => setShowCreateGoalModal(false)}
                        className="text-slate-400 hover:text-slate-600 p-1"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    <form onSubmit={handleCreateGoal} className="p-5 space-y-4 text-xs">
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Goal Title</label>
                        <input
                          type="text"
                          required
                          placeholder="e.g. Higher Education Fund, Home Down Payment"
                          value={newGoalForm.title}
                          onChange={(e) => setNewGoalForm({ ...newGoalForm, title: e.target.value })}
                          className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-blue-600 text-xs text-slate-900"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="font-semibold text-slate-700 block mb-1">Category</label>
                          <select
                            value={newGoalForm.category}
                            onChange={(e) => setNewGoalForm({ ...newGoalForm, category: e.target.value })}
                            className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-blue-600 text-xs text-slate-900 bg-white"
                          >
                            <option value="EMERGENCY">Emergency Fund</option>
                            <option value="VACATION">Vacation / Travel</option>
                            <option value="ASSET">Vehicle / Asset</option>
                            <option value="SAVINGS">General Wealth / Savings</option>
                            <option value="EDUCATION">Education / Career</option>
                          </select>
                        </div>

                        <div>
                          <label className="font-semibold text-slate-700 block mb-1">Target Amount (₹)</label>
                          <input
                            type="number"
                            required
                            min="10000"
                            value={newGoalForm.target_amount}
                            onChange={(e) =>
                              setNewGoalForm({ ...newGoalForm, target_amount: Number(e.target.value) })
                            }
                            className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-blue-600 text-xs text-slate-900"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="font-semibold text-slate-700 block mb-1">Monthly SIP (₹/mo)</label>
                          <input
                            type="number"
                            required
                            min="1000"
                            value={newGoalForm.monthly_allocation}
                            onChange={(e) =>
                              setNewGoalForm({ ...newGoalForm, monthly_allocation: Number(e.target.value) })
                            }
                            className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-blue-600 text-xs text-slate-900"
                          />
                        </div>

                        <div>
                          <label className="font-semibold text-slate-700 block mb-1">Target CAGR Return (%)</label>
                          <select
                            value={newGoalForm.target_return_cagr}
                            onChange={(e) =>
                              setNewGoalForm({ ...newGoalForm, target_return_cagr: Number(e.target.value) })
                            }
                            className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-blue-600 text-xs text-slate-900 bg-white"
                          >
                            <option value="6.5">Safe Liquid / FD (6.5%)</option>
                            <option value="9.5">Balanced Hybrid (9.5%)</option>
                            <option value="12.0">Nifty 50 Index (12.0%)</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Description (Optional)</label>
                        <input
                          type="text"
                          placeholder="Purpose or milestone details..."
                          value={newGoalForm.description}
                          onChange={(e) => setNewGoalForm({ ...newGoalForm, description: e.target.value })}
                          className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-blue-600 text-xs text-slate-900"
                        />
                      </div>

                      <div className="pt-2 flex justify-end space-x-2">
                        <button
                          type="button"
                          onClick={() => setShowCreateGoalModal(false)}
                          className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          className="px-4 py-1.5 rounded-lg bg-slate-900 text-white font-semibold hover:bg-slate-800 transition"
                        >
                          Create Goal
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </div>
          )}


          {activeTab === "insurance" && (
            <div className="space-y-6">
              {/* HEADER */}
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 truncate">
                    Insurance Planner
                  </h2>
                </div>
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => setShowAddPolicyModal(true)}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-xs transition cursor-pointer shrink-0"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Declare Policy</span>
                  </button>
                </div>
              </div>

              {/* 4 SUMMARY METRIC CARDS */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-4 min-w-0">
                {/* 1. Life Protection Cover & Gap */}
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Total Active Life Cover
                  </span>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight truncate block">
                      {(insurancePortfolio?.metrics?.total_life_cover || 0) >= 10000000
                        ? `₹${((insurancePortfolio?.metrics?.total_life_cover || 0) / 10000000).toFixed(2)} Cr`
                        : (insurancePortfolio?.metrics?.total_life_cover || 0) > 0
                        ? `₹${((insurancePortfolio?.metrics?.total_life_cover || 0) / 100000).toFixed(1)} L`
                        : "₹0.00 Cr"}
                    </span>
                  </div>
                  <p className="text-[11px] sm:text-xs text-slate-500 font-medium">
                    Required HLV: ₹{((insurancePortfolio?.metrics?.required_life_cover || 0) / 10000000).toFixed(2)} Cr
                    {(insurancePortfolio?.metrics?.life_protection_gap || 0) > 0 ? (
                      <span className="text-rose-600 font-semibold ml-1">
                        (₹{((insurancePortfolio?.metrics?.life_protection_gap || 0) / 10000000).toFixed(2)} Cr gap)
                      </span>
                    ) : (
                      <span className="text-emerald-600 font-semibold ml-1">(Adequately Protected)</span>
                    )}
                  </p>
                </div>

                {/* 2. Health Cover */}
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Total Health Cover
                  </span>
                  <div className="my-1.5 sm:my-2">
                    <span
                      className={`text-xl sm:text-2xl lg:text-3xl font-extrabold tracking-tight truncate block ${
                        (insurancePortfolio?.metrics?.total_health_cover || 0) > 0
                          ? "text-slate-900"
                          : "text-rose-600"
                      }`}
                    >
                      ₹{((insurancePortfolio?.metrics?.total_health_cover || 0) / 100000).toFixed(1)} L
                    </span>
                  </div>
                  <p className="text-[11px] sm:text-xs text-slate-500 font-medium">
                    {insurancePortfolio?.health_insurance?.has_employer_health_only ? (
                      <span className="text-amber-600 font-semibold">Corporate GMC Only</span>
                    ) : (insurancePortfolio?.metrics?.total_health_cover || 0) > 0 ? (
                      <span className="text-emerald-600 font-semibold">Retail Policy Active</span>
                    ) : (
                      <span className="text-rose-600 font-semibold">Zero Cover (High Risk)</span>
                    )}
                    {" • "}₹{(insurancePortfolio?.metrics?.out_of_pocket_medical_spent || 0).toLocaleString()} out-of-pocket
                  </p>
                </div>

                {/* 3. Annual Premium Outflow */}
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Annual Premium Outflow
                  </span>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight truncate block">
                      ₹{(insurancePortfolio?.metrics?.total_annual_premium || 0).toLocaleString()}
                      <span className="text-xs font-medium text-slate-400 ml-1">/ yr</span>
                    </span>
                  </div>
                  <p className="text-[11px] sm:text-xs text-slate-500 font-medium">
                    Across {insurancePortfolio?.unified_policies?.length || 0} active & detected {insurancePortfolio?.unified_policies?.length === 1 ? 'policy' : 'policies'}
                  </p>
                </div>

                {/* 4. Estimated Tax Saved */}
                <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                  <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Tax Savings (80C & 80D)
                  </span>
                  <div className="my-1.5 sm:my-2">
                    <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-emerald-600 tracking-tight truncate block">
                      ~₹{(insurancePortfolio?.metrics?.estimated_tax_savings || 0).toLocaleString()}
                      <span className="text-xs font-medium text-slate-400 ml-1">/ yr</span>
                    </span>
                  </div>
                  <p className="text-[11px] sm:text-xs text-slate-500 font-medium">
                    Deductions at 30% tax bracket
                  </p>
                </div>
              </div>

              {/* CRITICAL VULNERABILITY ALERTS */}
              {insurancePortfolio?.critical_alerts && insurancePortfolio.critical_alerts.length > 0 && (
                <div className="space-y-2">
                  {insurancePortfolio.critical_alerts.map((alert: string, idx: number) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-rose-50/80 border border-rose-200 text-xs text-rose-900 flex items-start space-x-2.5 shadow-xs"
                    >
                      <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                      <div className="leading-relaxed font-medium">{alert}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* UNIFIED POLICY VAULT (DETECTED & DECLARED) */}
              <div className="rounded-xl bg-white border border-slate-200 p-4 sm:p-6 space-y-4 shadow-sm">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <ShieldCheck className="w-5 h-5 text-slate-900" />
                      <h3 className="text-base font-bold text-slate-900">Active Insurance Portfolio</h3>
                      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-bold">
                        {insurancePortfolio?.unified_policies?.length || 0}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Combines debits detected from bank statements with off-statement declared policies (e.g. Employer GMC).
                    </p>
                  </div>

                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                    <div className="flex items-center space-x-1 p-1 rounded-lg bg-slate-100 border border-slate-200 text-xs overflow-x-auto no-scrollbar">
                      {(["ALL", "LIFE", "HEALTH", "MOTOR", "PERSONAL_ACCIDENT"] as const).map((cat) => (
                        <button
                          key={cat}
                          onClick={() => setPolicyFilter(cat)}
                          className={`px-2.5 py-1 rounded text-xs font-semibold transition shrink-0 ${
                            policyFilter === cat
                              ? "bg-white text-slate-900 shadow-xs"
                              : "text-slate-500 hover:text-slate-800"
                          }`}
                        >
                          {cat === "ALL" ? "All" : cat === "PERSONAL_ACCIDENT" ? "Accident" : cat}
                        </button>
                      ))}
                    </div>

                    <button
                      onClick={() => setShowCatalogDrawer(!showCatalogDrawer)}
                      className="px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition text-center shrink-0 cursor-pointer"
                    >
                      {showCatalogDrawer ? "Hide IRDAI Catalog" : "Inspect IRDAI Catalog"}
                    </button>
                  </div>
                </div>

                {/* POLICY CARDS GRID */}
                {insurancePortfolio?.unified_policies &&
                insurancePortfolio.unified_policies.filter(
                  (p: any) => policyFilter === "ALL" || p.category === policyFilter
                ).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {insurancePortfolio.unified_policies
                      .filter((p: any) => policyFilter === "ALL" || p.category === policyFilter)
                      .map((policy: any, idx: number) => (
                        <div
                          key={policy.id || idx}
                          className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-slate-300 transition shadow-xs space-y-3 relative group"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                                policy.badge === "STATEMENT VERIFIED"
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                  : policy.badge === "STATEMENT DETECTED"
                                  ? "bg-sky-50 text-sky-700 border-sky-200"
                                  : policy.badge === "EMPLOYER GMC"
                                  ? "bg-blue-50 text-blue-700 border-blue-200"
                                  : policy.badge === "AI ADOPTED"
                                  ? "bg-purple-50 text-purple-700 border-purple-200"
                                  : "bg-slate-100 text-slate-700 border-slate-200"
                              }`}
                            >
                              {policy.badge}
                            </span>
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                              {policy.category}
                            </span>
                          </div>

                          <div>
                            <h4 className="text-sm font-bold text-slate-900 leading-tight">
                              {policy.insurer_name}
                            </h4>
                            <p className="text-xs text-slate-600 mt-0.5">{policy.plan_name}</p>
                          </div>

                          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200/70 text-xs">
                            <div>
                              <span className="text-[10px] text-slate-400 font-semibold block">SUM INSURED</span>
                              <span className="font-bold text-slate-900">
                                ₹{Number(policy.sum_insured || 0).toLocaleString()}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] text-slate-400 font-semibold block">ANNUAL PREMIUM</span>
                              <span className="font-bold text-slate-900">
                                {Number(policy.annual_premium) > 0
                                  ? `₹${Number(policy.annual_premium).toLocaleString()}`
                                  : "Covered by Employer"}
                              </span>
                            </div>
                          </div>

                          {policy.covered_members && policy.covered_members.length > 0 && (
                            <div className="text-[11px] text-slate-500 flex items-center space-x-1">
                              <Users className="w-3 h-3 text-slate-400" />
                              <span>Members: {policy.covered_members.join(", ")}</span>
                            </div>
                          )}

                          {policy.is_traditional_endowment && (
                            <div className="p-2 rounded bg-amber-50 border border-amber-200 text-[11px] text-amber-800 leading-tight">
                              Traditional endowment policy detected. Low return (~4.5%) and limited death benefit.
                            </div>
                          )}

                          {policy.source && policy.source !== "STATEMENT_DETECTED" && (
                            <button
                              onClick={() => handleDeletePolicy(policy.id)}
                              className="text-[11px] text-rose-600 hover:text-rose-800 font-semibold pt-1 flex items-center space-x-1 transition"
                            >
                              <Trash2 className="w-3 h-3" />
                              <span>Remove declared policy</span>
                            </button>
                          )}
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="p-8 text-center rounded-xl bg-slate-50 border border-dashed border-slate-200 space-y-2">
                    <ShieldAlert className="w-8 h-8 text-slate-300 mx-auto" />
                    <p className="text-xs font-semibold text-slate-700">No active policies found for this filter</p>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      Add an off-statement corporate GMC policy or upload statements with insurance premium debits.
                    </p>
                    <button
                      onClick={() => setShowAddPolicyModal(true)}
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition mt-2"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Declare Off-Statement Policy</span>
                    </button>
                  </div>
                )}
              </div>

              {/* CURATED IRDAI CATALOG DRAWER (EXPANDABLE) */}
              {showCatalogDrawer && (
                <div className="rounded-xl bg-white border border-slate-200 p-6 space-y-5 shadow-sm">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center space-x-2">
                      <Building2 className="w-5 h-5 text-blue-600" />
                      <div>
                        <h3 className="text-base font-bold text-slate-900">
                          Curated Indian Insurance Products Knowledge Base
                        </h3>
                        <p className="text-xs text-slate-500">
                          Verified IRDAI metrics, 3-year Claim Settlement Ratios (CSR), room rent clauses & network size.
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
                      {insuranceCatalog.length} Top-Tier Plans
                    </span>
                  </div>

                  {/* CATEGORY FILTER TABS */}
                  <div className="flex items-center space-x-1.5 overflow-x-auto p-1 rounded-lg bg-slate-100 border border-slate-200 text-xs">
                    {[
                      { key: "ALL", label: "All Products" },
                      { key: "LIFE_TERM", label: "Pure Term Life" },
                      { key: "HEALTH_COMPREHENSIVE", label: "Retail Health" },
                      { key: "HEALTH_SUPER_TOPUP", label: "Super Top-Up" },
                      { key: "PERSONAL_ACCIDENT", label: "Personal Accident" },
                      { key: "MOTOR_COMPREHENSIVE", label: "Motor" },
                    ].map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setCatalogFilter(tab.key)}
                        className={`px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap transition ${
                          catalogFilter === tab.key
                            ? "bg-white text-slate-900 shadow-xs"
                            : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* CATALOG PRODUCTS GRID */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {insuranceCatalog
                      .filter((prod) => catalogFilter === "ALL" || prod.category === catalogFilter)
                      .map((prod) => (
                        <div
                          key={prod.id}
                          className="p-4 rounded-xl border border-slate-200 bg-slate-50/40 hover:bg-white hover:border-slate-300 space-y-3 text-xs shadow-xs transition"
                        >
                          <div className="flex justify-between items-start gap-2">
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                              {prod.category_label || prod.category}
                            </span>
                            <div className="flex flex-wrap gap-1 justify-end">
                              {prod.csr_3yr_avg && (
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                                  CSR {prod.csr_3yr_avg}%
                                </span>
                              )}
                              {prod.asr_percentage && (
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200">
                                  ASR {prod.asr_percentage}%
                                </span>
                              )}
                              {prod.icr_percentage && (
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                                  ICR {prod.icr_percentage}%
                                </span>
                              )}
                              {prod.solvency_ratio && (
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                                  Solv {prod.solvency_ratio}x
                                </span>
                              )}
                            </div>
                          </div>

                          <div>
                            <div className="font-bold text-slate-900 text-sm leading-snug">{prod.insurer}</div>
                            <div className="text-slate-600 font-medium">{prod.product_name}</div>
                          </div>

                          {/* PILLS ROW FOR ROOM RENT & NETWORKS */}
                          <div className="flex flex-wrap gap-1.5 text-[10px] font-medium">
                            {prod.zero_room_rent_capping !== undefined && (
                              <span
                                className={`px-2 py-0.5 rounded-full border ${
                                  prod.zero_room_rent_capping
                                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                                    : "bg-amber-50 text-amber-800 border-amber-200"
                                }`}
                              >
                                {prod.zero_room_rent_capping ? "✓ Zero Room Rent Cap" : "Room Rent Sub-limit"}
                              </span>
                            )}
                            {prod.network_hospitals_count && (
                              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                                {prod.network_hospitals_count.toLocaleString()}+ Hospitals
                              </span>
                            )}
                            {prod.ped_waiting_period_years && (
                              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                                PED: {prod.ped_waiting_period_years}y
                              </span>
                            )}
                            {prod.co_pay && (
                              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                                Co-pay: {prod.co_pay}
                              </span>
                            )}
                          </div>

                          {prod.key_features && (
                            <ul className="space-y-1 text-slate-600 text-[11px] list-disc list-inside">
                              {prod.key_features.slice(0, 3).map((f: string, i: number) => (
                                <li key={i}>{f}</li>
                              ))}
                            </ul>
                          )}

                          <div className="pt-2 border-t border-slate-200/70 text-[11px] text-slate-600 leading-tight">
                            <span className="font-semibold text-slate-800">Fiduciary Suitability: </span>
                            {prod.suitability}
                          </div>

                          {/* PRICING ESTIMATE SAMPLE */}
                          {(prod.approx_annual_premium_age_35_1cr ||
                            prod.approx_annual_premium_individual_10L_age_30 ||
                            prod.approx_annual_premium_25L_5L_deductible ||
                            prod.approx_annual_premium_50L ||
                            prod.approx_annual_premium_hatchback) && (
                            <div className="pt-2 border-t border-slate-100 flex justify-between items-center text-[11px]">
                              <span className="text-slate-400">Benchmark Premium:</span>
                              <span className="font-bold text-slate-900">
                                {prod.approx_annual_premium_age_35_1cr
                                  ? `~₹${prod.approx_annual_premium_age_35_1cr.toLocaleString()}/yr (Age 35, ₹1Cr)`
                                  : prod.approx_annual_premium_individual_10L_age_30
                                  ? `~₹${prod.approx_annual_premium_individual_10L_age_30.toLocaleString()}/yr (Age 30, ₹10L)`
                                  : prod.approx_annual_premium_25L_5L_deductible
                                  ? `~₹${prod.approx_annual_premium_25L_5L_deductible.toLocaleString()}/yr (₹25L, ₹5L Ded)`
                                  : prod.approx_annual_premium_50L
                                  ? `~₹${prod.approx_annual_premium_50L.toLocaleString()}/yr (₹50L PA)`
                                  : `~₹${prod.approx_annual_premium_hatchback?.toLocaleString()}/yr`}
                              </span>
                            </div>
                          )}

                          <div className="text-[10px] text-emerald-700 font-semibold">{prod.tax_benefit}</div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* INTERACTIVE HLV CALCULATOR */}
              <div className="rounded-xl bg-white border border-slate-200 p-4 sm:p-6 space-y-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center space-x-2">
                    <Umbrella className="w-5 h-5 text-blue-600 shrink-0" />
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Interactive Needs-Based Human Life Value (HLV) Calculator
                      </h3>
                    </div>
                  </div>

                  {insurancePortfolio?.metrics?.is_income_from_statement && (
                    <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold self-start sm:self-auto shrink-0">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Grounded in Ledger Inflow</span>
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  <div className="lg:col-span-2 space-y-5">
                    {/* SLIDER 1: ANNUAL INCOME */}
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="min-w-0">
                          <span className="text-xs font-semibold text-slate-800 leading-tight block">
                            Annual Take-Home Income
                          </span>
                          {insurancePortfolio?.metrics?.is_income_from_statement && (
                            <span className="inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                              ₹{Math.round(insurancePortfolio.cashflow_context?.monthly_inflow || hlvIncome / 12).toLocaleString()}/mo statement
                            </span>
                          )}
                        </div>
                        <span className="text-sm sm:text-base font-bold text-blue-600 shrink-0">
                          ₹{hlvIncome.toLocaleString()}
                        </span>
                      </div>
                      <input
                        type="range"
                        min="50000"
                        max="10000000"
                        step="25000"
                        value={hlvIncome}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setHlvIncome(val);
                          handleRecalculateHlv(val, undefined, undefined, undefined, undefined);
                        }}
                        className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
                      />
                      <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
                        <span>₹50k</span>
                        <span>₹25 Lakhs</span>
                        <span>₹50 Lakhs</span>
                        <span>₹1 Crore</span>
                      </div>
                    </div>

                    {/* SLIDER 2: INCOME MULTIPLIER */}
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <span className="text-xs font-semibold text-slate-800">Income Replacement Multiplier</span>
                        <span className="text-sm sm:text-base font-bold text-purple-600 shrink-0">{hlvMultiplier}x Annual Income</span>
                      </div>
                      <input
                        type="range"
                        min="8"
                        max="20"
                        step="1"
                        value={hlvMultiplier}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setHlvMultiplier(val);
                          handleRecalculateHlv(undefined, undefined, undefined, undefined, val);
                        }}
                        className="w-full accent-purple-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
                      />
                      <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
                        <span>8x (Minimal)</span>
                        <span>12x - 15x (Recommended Standard)</span>
                        <span>20x (Maximum Security)</span>
                      </div>
                    </div>

                    {/* SLIDER 3: OUTSTANDING LOANS */}
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="min-w-0">
                          <span className="text-xs font-semibold text-slate-800 leading-tight block">
                            Outstanding Debt & Loan Liabilities (Home / Car / Personal)
                          </span>
                          {insurancePortfolio?.metrics?.is_loans_from_statement && (
                            <span className="inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                              Detected from EMIs
                            </span>
                          )}
                        </div>
                        <span className="text-sm sm:text-base font-bold text-rose-600 shrink-0">
                          ₹{hlvLoans.toLocaleString()}
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="20000000"
                        step="25000"
                        value={hlvLoans}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setHlvLoans(val);
                          handleRecalculateHlv(undefined, val, undefined, undefined, undefined);
                        }}
                        className="w-full accent-rose-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
                      />
                      <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
                        <span>₹0 Debt</span>
                        <span>₹50 Lakhs</span>
                        <span>₹1 Crore</span>
                        <span>₹2 Crores</span>
                      </div>
                    </div>

                    {/* SLIDER 4: LIQUID ASSETS */}
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="min-w-0">
                          <span className="text-xs font-semibold text-slate-800 leading-tight block">
                            Existing Liquid Savings & Cushion (Bank Balance / Sweep / MFs)
                          </span>
                          {insurancePortfolio?.metrics?.is_assets_from_statement && (
                            <span className="inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Statement Ending Balance
                            </span>
                          )}
                        </div>
                        <span className="text-sm sm:text-base font-bold text-emerald-600 shrink-0">
                          ₹{hlvAssets.toLocaleString()}
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="10000000"
                        step="25000"
                        value={hlvAssets}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setHlvAssets(val);
                          handleRecalculateHlv(undefined, undefined, val, undefined, undefined);
                        }}
                        className="w-full accent-emerald-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
                      />
                      <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
                        <span>₹0</span>
                        <span>₹25 Lakhs</span>
                        <span>₹50 Lakhs</span>
                        <span>₹1 Crore</span>
                      </div>
                    </div>

                    {/* SLIDER 5: NUMBER OF DEPENDENTS */}
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <span className="text-xs font-semibold text-slate-800">Number of Financial Dependents</span>
                        <span className="text-sm sm:text-base font-bold text-slate-900 shrink-0">{hlvDependents} Members</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="5"
                        step="1"
                        value={hlvDependents}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setHlvDependents(val);
                          handleRecalculateHlv(undefined, undefined, undefined, val, undefined);
                        }}
                        className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
                      />
                      <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
                        <span>0 (Single)</span>
                        <span>1</span>
                        <span>2 (Standard Family)</span>
                        <span>3</span>
                        <span>4+ (Elderly Parents + Kids)</span>
                      </div>
                    </div>
                  </div>

                  {/* CALCULATOR RESULT CARD */}
                  <div className="p-4 sm:p-6 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-6">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                        Pure Term Life Requirement
                      </span>
                      <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                        {hlvRequiredCover >= 10000000
                          ? `₹${(hlvRequiredCover / 10000000).toFixed(2)} Crores`
                          : `₹${(hlvRequiredCover / 100000).toFixed(1)} Lakhs`}
                      </div>
                      <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                        Replaces {hlvMultiplier} years of income and wipes out ₹{hlvLoans.toLocaleString()} in debt.
                      </p>
                    </div>

                    <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-600">Active Life Cover:</span>
                        <span className="font-bold text-slate-900">
                          {detectedCover >= 10000000
                            ? `₹${(detectedCover / 10000000).toFixed(2)} Cr`
                            : `₹${(detectedCover / 100000).toFixed(1)} L`}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-600">Net Protection Gap:</span>
                        <span
                          className={`font-bold ${
                            hlvGap > 0 ? "text-rose-600" : "text-emerald-600"
                          }`}
                        >
                          {hlvGap <= 0
                            ? "Adequately Covered"
                            : hlvGap >= 10000000
                            ? `₹${(hlvGap / 10000000).toFixed(2)} Cr`
                            : `₹${(hlvGap / 100000).toFixed(1)} L`}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs pt-1 border-t border-slate-100">
                        <span className="text-slate-600">Est. Pure Term Cost:</span>
                        <span className="font-bold text-emerald-700">
                          ~₹{estTermAnnualPremium.toLocaleString()}/yr
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-600">Monthly Equivalent:</span>
                        <span className="font-bold text-emerald-600">
                          ~₹{estTermMonthlyPremium.toLocaleString()}/mo
                        </span>
                      </div>
                    </div>

                    <div className="text-[11px] text-slate-500 bg-blue-50 border border-blue-200/60 p-3 rounded-lg leading-relaxed">
                      Pure term insurance provides uncompromised risk protection without endowment commissions. Eligible for Section 80C tax deduction.
                    </div>
                  </div>
                </div>
              </div>

              {/* TRADITIONAL ENDOWMENT ARBITRAGE BOX */}
              {insurancePortfolio?.arbitrage?.endowment_annual_premium > 0 && (
                <div className="p-4 sm:p-6 rounded-xl bg-white border border-amber-200 shadow-sm space-y-4">
                  <div className="flex items-center space-x-2">
                    <BadgePercent className="w-5 h-5 text-amber-600 shrink-0" />
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Endowment vs Pure Term Arbitrage Opportunity
                      </h3>
                      <p className="text-xs text-slate-500">
                        Detected LIC Traditional Endowment debit: ₹
                        {insurancePortfolio.arbitrage.endowment_annual_premium.toLocaleString()}/yr
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200 space-y-1">
                      <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider">
                        Current Endowment Path
                      </span>
                      <div className="text-base sm:text-lg font-bold text-slate-900">
                        ₹{(insurancePortfolio.arbitrage.endowment_coverage_provided / 100000).toFixed(1)} Lakhs Cover
                      </div>
                      <p className="text-xs text-slate-600">
                        Maturity at ~4.5% returns: ~₹
                        {insurancePortfolio.arbitrage.endowment_maturity_est.toLocaleString()}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 space-y-1">
                      <span className="text-[10px] font-bold text-blue-800 uppercase tracking-wider">
                        Pure Term + Nifty 50 Index Fund
                      </span>
                      <div className="text-base sm:text-lg font-bold text-slate-900">
                        ₹{(insurancePortfolio.arbitrage.term_coverage_provided / 10000000).toFixed(1)} Cr Cover
                      </div>
                      <p className="text-xs text-slate-600">
                        Index Fund Value at 12% CAGR: ~₹
                        {insurancePortfolio.arbitrage.index_fund_future_value.toLocaleString()}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 space-y-1">
                      <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">
                        Net Wealth Advantage
                      </span>
                      <div className="text-base sm:text-lg font-bold text-emerald-700">
                        +₹{insurancePortfolio.arbitrage.wealth_advantage.toLocaleString()} Extra Wealth
                      </div>
                      <p className="text-xs text-slate-600 font-medium">Plus 10X higher immediate family death cover</p>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-amber-50/50 border border-amber-200 text-xs text-amber-900 leading-relaxed">
                    <span className="font-bold">Fiduciary Rule of Thumb:</span> Never mix insurance with investment.
                    Surrendering or making a low-yield traditional policy paid-up and redirecting future premiums into Pure
                    Term + Nifty 50 Index Funds delivers massive compounding wealth and genuine risk protection.
                  </div>
                </div>
              )}

              {/* GEMINI AI RECOMMENDATIONS HUB */}
              <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center space-x-2">
                    <Bot className="w-5 h-5 text-purple-600" />
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        AI Fiduciary Insurance Advisor
                      </h3>
                      <p className="text-xs text-slate-500">
                        Zero commissions. Evaluates your real statement surplus, debt obligations, and corporate GMC status.
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={handleGenerateAiRecommendations}
                    disabled={insuranceAiLoading}
                    className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold shadow-xs transition disabled:opacity-50 shrink-0 cursor-pointer"
                  >
                    {insuranceAiLoading ? (
                      <>
                        <RefreshCcw className="w-3.5 h-3.5 animate-spin" />
                        <span>Auditing Statement Cashflow...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Generate Cashflow-Grounded Advice</span>
                      </>
                    )}
                  </button>
                </div>

                {aiRecommendations ? (
                  <div className="space-y-4 pt-2">
                    {/* Summary Verdict */}
                    <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-200/80 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-purple-900 uppercase tracking-wider">
                          Advisor Diagnosis Verdict
                        </span>
                        <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800">
                          Fiduciary Review
                        </span>
                      </div>
                      <p className="text-xs text-purple-950 leading-relaxed font-medium">
                        {aiRecommendations.summary_verdict}
                      </p>

                      {aiRecommendations.primary_vulnerabilities && (
                        <div className="pt-2 border-t border-purple-200/60 space-y-1">
                          <span className="text-[10px] font-bold text-purple-800 uppercase tracking-wider block">
                            Key Identified Vulnerabilities:
                          </span>
                          <ul className="list-disc list-inside text-xs text-purple-900 space-y-0.5">
                            {aiRecommendations.primary_vulnerabilities.map((v: string, i: number) => (
                              <li key={i}>{v}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Prioritized Recommendation Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {aiRecommendations.recommendations?.map((rec: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-white transition shadow-xs space-y-3 flex flex-col justify-between"
                        >
                          <div className="space-y-3">
                            <div className="flex justify-between items-center">
                              <span className="w-6 h-6 rounded-full bg-slate-900 text-white flex items-center justify-center text-xs font-bold">
                                {rec.priority || idx + 1}
                              </span>
                              <div className="flex items-center space-x-1">
                                {rec.is_super_topup_bridge && (
                                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                                    ⚡ Corporate Bridge
                                  </span>
                                )}
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                  {rec.category}
                                </span>
                              </div>
                            </div>

                            <div>
                              <h4 className="text-xs font-bold text-slate-900 leading-snug">
                                {rec.action_title}
                              </h4>
                              <div className="text-[11px] text-purple-700 font-semibold mt-1">
                                Matched: {rec.matched_product_name}
                              </div>
                              {rec.key_metric_badge && (
                                <div className="mt-1">
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                                    {rec.key_metric_badge}
                                  </span>
                                </div>
                              )}
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-slate-200">
                              <div>
                                <span className="text-[10px] text-slate-400 block font-medium">TARGET COVER</span>
                                <span className="font-bold text-slate-900">
                                  ₹{Number(rec.recommended_sum_insured || 0).toLocaleString()}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 block font-medium">EST. COST</span>
                                <span className="font-bold text-slate-900">
                                  ~₹{Number(rec.estimated_annual_cost || 0).toLocaleString()}
                                  <span className="text-[10px] font-normal text-slate-400">/yr</span>
                                </span>
                                <span className="text-[10px] text-emerald-700 font-medium block">
                                  (~₹{Math.round(rec.estimated_monthly_cost || rec.estimated_annual_cost / 12).toLocaleString()}/mo)
                                </span>
                              </div>
                            </div>

                            <p className="text-xs text-slate-600 leading-relaxed">{rec.rationale}</p>
                          </div>

                          <div className="space-y-2 pt-2 border-t border-slate-200/70">
                            {/* AFFORDABILITY AUDIT CALLOUT */}
                            {rec.affordability_audit && (
                              <div className="p-2.5 rounded-lg bg-emerald-50/80 border border-emerald-200 text-[11px] text-emerald-950 leading-snug">
                                <span className="font-bold flex items-center space-x-1 text-emerald-900 mb-0.5">
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                                  <span>Affordability Audit:</span>
                                </span>
                                {rec.affordability_audit}
                              </div>
                            )}

                            <div className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200/60 p-2 rounded">
                              {rec.tax_benefit}
                            </div>

                            {/* ADOPT POLICY BUTTON */}
                            {isRecAlreadyAdopted(rec) ? (
                              <div className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-xs">
                                <span className="font-semibold text-emerald-800 flex items-center space-x-1.5">
                                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                                  <span>Active in Portfolio</span>
                                </span>
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 uppercase tracking-wider">
                                  Adopted ✓
                                </span>
                              </div>
                            ) : (
                              <button
                                onClick={() => handleAdoptRecommendation(rec, idx)}
                                disabled={adoptingRecIdx === idx}
                                className="w-full inline-flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 active:scale-[0.99] text-white text-xs font-semibold shadow-xs transition disabled:opacity-50 cursor-pointer"
                              >
                                {adoptingRecIdx === idx ? (
                                  <>
                                    <RefreshCcw className="w-3.5 h-3.5 animate-spin" />
                                    <span>Adding Policy to Portfolio...</span>
                                  </>
                                ) : (
                                  <>
                                    <Plus className="w-3.5 h-3.5" />
                                    <span>Add Policy to Portfolio</span>
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    {aiRecommendations.arbitrage_guidance && (
                      <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 leading-relaxed">
                        <span className="font-bold">Endowment Arbitrage Guidance: </span>
                        {aiRecommendations.arbitrage_guidance}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-8 text-center rounded-xl bg-slate-50 border border-dashed border-slate-200 space-y-2">
                    <Bot className="w-8 h-8 text-slate-300 mx-auto" />
                    <p className="text-xs font-semibold text-slate-700">Ready to run fiduciary advisor</p>
                    <p className="text-xs text-slate-400 max-w-md mx-auto">
                      Click the button above to evaluate your statement debits, declared policies, and loan EMIs against
                      our curated Indian insurance catalog.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}


          {activeTab === "spend" && (
            <div className="space-y-4 sm:space-y-6">
              {/* TITLE (SINGLE ROW) AND MONTHS SCROLLBAR BELOW */}
              <div className="space-y-3">
                <h2 className="text-xl font-bold text-slate-900 whitespace-nowrap">Monthly Consumption Drilldown</h2>

                {/* MONTHS HORIZONTAL SCROLL BAR */}
                <div className="flex items-center space-x-1 overflow-x-auto no-scrollbar p-1 rounded-lg bg-white border border-slate-200 shadow-xs w-full max-w-full">
                  {availableMonths.map((m) => (
                    <button
                      key={m}
                      onClick={() => setSelectedMonth(m)}
                      className={`px-3 py-1 rounded text-xs font-semibold transition shrink-0 ${
                        selectedMonth === m
                          ? "bg-slate-900 text-white shadow-xs"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              {monthLoading || !monthDetail ? (
                <div className="p-16 flex flex-col items-center justify-center text-slate-400">
                  <Activity className="w-6 h-6 text-slate-600 animate-spin mb-2" />
                  <span className="text-xs">Loading data for {selectedMonth}...</span>
                </div>
              ) : (
                <div className="space-y-4 sm:space-y-6">
                  {/* MONTH HIGHLIGHT CARDS (2x2 on mobile, 4 cols on desktop) */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-4 min-w-0">
                    <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                      <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400 truncate block">Month Inflow</span>
                      <div className="my-1.5 sm:my-2">
                        <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-emerald-600 tracking-tight truncate block">
                          ₹{Number(monthDetail?.inflow || 0).toLocaleString()}
                        </span>
                      </div>
                      <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">Total deposits for {selectedMonth}</span>
                    </div>

                    <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                      <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400 truncate block">Month Outflow Burn</span>
                      <div className="my-1.5 sm:my-2">
                        <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-blue-600 tracking-tight truncate block">
                          ₹{Number(monthDetail?.outflow || 0).toLocaleString()}
                        </span>
                      </div>
                      <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">Total debits for {selectedMonth}</span>
                    </div>

                    <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                      <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400 truncate block">Net Surplus Added</span>
                      <div className="my-1.5 sm:my-2">
                        <span className={`text-xl sm:text-2xl lg:text-3xl font-extrabold tracking-tight truncate block ${(monthDetail?.net_savings || 0) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                          ₹{Number(monthDetail?.net_savings || 0).toLocaleString()}
                        </span>
                      </div>
                      <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">Monthly savings accumulation</span>
                    </div>

                    <div className="p-3.5 sm:p-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
                      <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-slate-400 truncate block">Transactions</span>
                      <div className="my-1.5 sm:my-2">
                        <span className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight truncate block">
                          {monthDetail?.transaction_count || 0}
                        </span>
                      </div>
                      <span className="text-[11px] sm:text-xs font-medium text-slate-500 truncate">Statement records parsed</span>
                    </div>
                  </div>

                  {/* AI MONTHLY INSIGHTS TRIGGER & DIAGNOSTIC PANEL */}
                  {(() => {
                    const activeInsight = monthInsightsMap[selectedMonth];
                    const obsList = activeInsight?.observations || activeInsight?.key_findings || [];
                    return (
                      <div className="space-y-4">
                        {!activeInsight ? (
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-white border border-slate-200 shadow-xs gap-4">
                            <div className="flex items-center space-x-3.5">
                              <div className="w-9 h-9 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0 text-indigo-600">
                                <Sparkles className="w-4 h-4" />
                              </div>
                              <div>
                                <div className="flex items-center space-x-2">
                                  <h4 className="text-sm font-bold text-slate-900">Generate Monthly Insights</h4>
                                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-600">
                                    {selectedMonth}
                                  </span>
                                </div>
                                <p className="text-xs text-slate-500 mt-0.5">
                                  Audit capital transfers, category concentrations, chart spikes, and daily spending velocity
                                </p>
                              </div>
                            </div>

                            <button
                              onClick={() => handleGenerateInsights(selectedMonth)}
                              disabled={isGeneratingInsights}
                              className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs transition shadow-xs flex items-center justify-center space-x-2 shrink-0 disabled:opacity-75 disabled:cursor-not-allowed cursor-pointer"
                            >
                              {isGeneratingInsights ? (
                                <>
                                  <Activity className="w-3.5 h-3.5 text-white animate-spin" />
                                  <span>Analyzing transactions...</span>
                                </>
                              ) : (
                                <>
                                  <Sparkles className="w-3.5 h-3.5 text-indigo-300" />
                                  <span>Generate Insights</span>
                                </>
                              )}
                            </button>
                          </div>
                        ) : (
                          <div className="rounded-xl bg-white border border-slate-200 shadow-xs overflow-hidden">
                            {/* Blackish Header: Differentiates diagnostic header from observations */}
                            <div className="p-4 sm:p-5 bg-slate-900 border-b border-slate-800 text-white flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                              <div className="space-y-1.5 min-w-0">
                                <div className="flex items-center space-x-2 flex-wrap gap-y-1.5">
                                  <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-white/10 text-slate-200 border border-white/15">
                                    {selectedMonth} Financial Diagnostic
                                  </span>
                                  <h3 className="text-sm md:text-base font-bold text-white tracking-tight">
                                    {renderHighlightedText(activeInsight.executive_headline, "text-emerald-400 font-extrabold")}
                                  </h3>
                                </div>
                                <p className="text-xs text-slate-300 leading-relaxed pt-0.5">
                                  {renderHighlightedText(activeInsight.verdict_summary, "text-white font-bold")}
                                </p>
                              </div>

                              <button
                                onClick={() => handleGenerateInsights(selectedMonth)}
                                disabled={isGeneratingInsights}
                                className="self-end sm:self-auto px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold flex items-center space-x-1.5 transition shrink-0 disabled:opacity-50 cursor-pointer shadow-xs"
                              >
                                <RefreshCcw className={`w-3.5 h-3.5 text-slate-300 ${isGeneratingInsights ? "animate-spin" : ""}`} />
                                <span>{isGeneratingInsights ? "Analyzing..." : "Re-Analyze"}</span>
                              </button>
                            </div>

                            {/* White Observations & Directive Section */}
                            <div className="p-4 sm:p-5 space-y-4">
                              {/* Row-by-Row Observations Feed */}
                            <div className="divide-y divide-slate-100">
                              {obsList.map((item: any, idx: number) => {
                                const sev = item.severity || item.type || "info";
                                const pillClass =
                                  sev === "danger"
                                    ? "bg-rose-50 text-rose-700 border-rose-200"
                                    : sev === "warning"
                                    ? "bg-amber-50 text-amber-700 border-amber-200"
                                    : sev === "success"
                                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                    : "bg-blue-50 text-blue-700 border-blue-200";

                                return (
                                  <div
                                    key={idx}
                                    className="py-3.5 first:pt-1 last:pb-1 flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-4"
                                  >
                                    <div className="sm:w-44 shrink-0 pt-0.5">
                                      <span className={`inline-block text-[11px] font-semibold px-2.5 py-0.5 rounded border ${pillClass}`}>
                                        {stripMarkdown(item.tag || item.badge || "Observation")}
                                      </span>
                                    </div>
                                    <div className="flex-1 space-y-0.5">
                                      <h5 className="text-xs font-bold text-slate-900">
                                        {stripMarkdown(item.title)}
                                      </h5>
                                      <p className="text-xs text-slate-600 leading-relaxed">
                                        {renderHighlightedText(item.detail)}
                                      </p>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>

                            {/* Fiduciary Directive (Clean light callout) */}
                            {activeInsight.fiduciary_recommendation && (
                              <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-amber-950 flex items-start space-x-3">
                                <Zap className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                                <div className="text-xs leading-relaxed">
                                  <span className="font-bold text-amber-900 mr-1.5">
                                    Fiduciary Directive:
                                  </span>
                                  <span className="text-amber-900/90">
                                    {renderHighlightedText(activeInsight.fiduciary_recommendation)}
                                  </span>
                                </div>
                              </div>
                            )}
                            </div>
                          </div>
                        )}

                        {insightsError && (
                          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
                            <AlertTriangle className="w-4 h-4 shrink-0" />
                            <span>{insightsError}</span>
                          </div>
                        )}
                      </div>
                    );
                  })()}

                  {/* CHARTS */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 mb-1">Expenses by Category</h3>
                        <p className="text-xs text-slate-500 mb-3">{selectedMonth}</p>
                        <div className="h-48 w-full flex items-center justify-center">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={monthDetail.subcategories}
                                cx="50%"
                                cy="50%"
                                innerRadius={45}
                                outerRadius={70}
                                paddingAngle={3}
                                dataKey="value"
                              >
                                {monthDetail.subcategories.map((_: any, index: number) => (
                                  <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip
                                contentStyle={{ backgroundColor: "#FFFFFF", borderColor: "#E2E8F0", borderRadius: "8px", fontSize: "12px" }}
                                formatter={(v: any) => [`₹${Number(v).toLocaleString()}`, "Spend"]}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      <div className="space-y-1 mt-2 pt-2 border-t border-slate-100 max-h-40 overflow-y-auto pr-1">
                        {monthDetail.subcategories.map((s: any, idx: number) => {
                          const isSelected = ledgerCategoryFilter === s.name;
                          return (
                            <div
                              key={idx}
                              onClick={() => {
                                setLedgerCategoryFilter((prev) => (prev === s.name ? "all" : s.name));
                              }}
                              className={`flex items-center justify-between text-xs px-2 py-1 rounded-md cursor-pointer transition ${
                                isSelected ? "bg-slate-900 text-white font-semibold" : "hover:bg-slate-50 text-slate-600"
                              }`}
                              title={`Click to filter ledger by ${s.name}`}
                            >
                              <div className="flex items-center space-x-1.5 truncate">
                                <span
                                  className="w-2 h-2 rounded-full shrink-0"
                                  style={{
                                    backgroundColor: isSelected ? "#FFFFFF" : CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
                                  }}
                                />
                                <span className={`truncate ${isSelected ? "text-white" : "text-slate-600"}`}>{s.name}</span>
                              </div>
                              <span className={`font-semibold ${isSelected ? "text-white" : "text-slate-900"}`}>
                                ₹{s.value.toLocaleString()}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="lg:col-span-2 p-5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 mb-1">Daily Burn Rate</h3>
                        <p className="text-xs text-slate-500 mb-3">{selectedMonth}</p>
                        <div className="h-68 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={monthDetail.daily_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <XAxis dataKey="day" stroke="#94A3B8" fontSize={10} tickLine={false} />
                              <YAxis stroke="#94A3B8" fontSize={10} tickLine={false} tickFormatter={(v) => `₹${v / 1000}k`} />
                              <Tooltip
                                contentStyle={{ backgroundColor: "#FFFFFF", borderColor: "#E2E8F0", borderRadius: "8px", fontSize: "12px" }}
                                formatter={(v: any) => [`₹${Number(v).toLocaleString()}`, "Spend"]}
                              />
                              <Bar dataKey="spend" fill="#2563EB" radius={[4, 4, 0, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* TRANSACTIONS TABLE WITH SORTING & CATEGORY FILTER */}
                  {(() => {
                    let txs = (monthDetail.transactions || []).filter((t: any) => {
                      const matchSearch =
                        !searchTerm ||
                        t.narration.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        t.sub_category.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        (t.merchant && t.merchant.toLowerCase().includes(searchTerm.toLowerCase()));

                      const matchCategory =
                        ledgerCategoryFilter === "all" ||
                        t.sub_category === ledgerCategoryFilter ||
                        t.category === ledgerCategoryFilter;

                      return matchSearch && matchCategory;
                    });

                    txs = [...txs].sort((a: any, b: any) => {
                      let comp = 0;
                      if (ledgerSortField === "date") {
                        comp = a.date.localeCompare(b.date);
                      } else if (ledgerSortField === "category") {
                        comp = (a.sub_category || "").localeCompare(b.sub_category || "");
                      } else if (ledgerSortField === "debit") {
                        comp = (Number(a.debit) || 0) - (Number(b.debit) || 0);
                      }

                      return ledgerSortDir === "asc" ? comp : -comp;
                    });

                    const filteredTotalDebit = txs.reduce((sum: number, t: any) => sum + (Number(t.debit) || 0), 0);

                    return (
                      <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-4">
                        {/* TOOLBAR */}
                        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                          <div className="flex items-center space-x-2">
                            <h3 className="text-sm font-bold text-slate-900">Transactions Ledger</h3>
                            <span className="text-xs text-slate-400 font-medium">
                              ({txs.length} of {monthDetail.transactions.length})
                            </span>
                          </div>

                          <div className="flex items-center flex-wrap gap-2">
                            {/* CATEGORY FILTER DROPDOWN */}
                            <div className="relative">
                              <select
                                value={ledgerCategoryFilter}
                                onChange={(e) => setLedgerCategoryFilter(e.target.value)}
                                className="text-xs font-medium pl-3 pr-8 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-1 focus:ring-slate-900 transition cursor-pointer"
                              >
                                <option value="all">All Categories</option>
                                {monthDetail.subcategories?.map((s: any) => (
                                  <option key={s.name} value={s.name}>
                                    {s.name} (₹{s.value.toLocaleString()})
                                  </option>
                                ))}
                              </select>
                            </div>

                            {/* SORT BY CATEGORY BUTTON */}
                            <button
                              onClick={() => toggleSort("category")}
                              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition flex items-center space-x-1.5 cursor-pointer shadow-xs ${
                                ledgerSortField === "category"
                                  ? "bg-slate-900 text-white border-slate-900"
                                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                              }`}
                              title="Sort by Category"
                            >
                              <Filter className="w-3.5 h-3.5" />
                              <span>Category</span>
                              <span className="text-[10px] ml-0.5 font-bold">
                                {ledgerSortField === "category" ? (ledgerSortDir === "asc" ? "A→Z" : "Z→A") : ""}
                              </span>
                            </button>

                            {/* SORT BY DATE BUTTON */}
                            <button
                              onClick={() => toggleSort("date")}
                              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition flex items-center space-x-1.5 cursor-pointer shadow-xs ${
                                ledgerSortField === "date"
                                  ? "bg-slate-900 text-white border-slate-900"
                                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                              }`}
                              title="Sort by Date"
                            >
                              <Calendar className="w-3.5 h-3.5" />
                              <span>Date</span>
                              <span className="text-[10px] ml-0.5 font-bold">
                                {ledgerSortField === "date" ? (ledgerSortDir === "desc" ? "Newest" : "Oldest") : ""}
                              </span>
                            </button>

                            {/* SORT BY DEBIT AMOUNT BUTTON */}
                            <button
                              onClick={() => toggleSort("debit")}
                              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition flex items-center space-x-1.5 cursor-pointer shadow-xs ${
                                ledgerSortField === "debit"
                                  ? "bg-slate-900 text-white border-slate-900"
                                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                              }`}
                              title="Sort by Amount (Debit)"
                            >
                              <TrendingUp className="w-3.5 h-3.5" />
                              <span>Amount</span>
                              <span className="text-[10px] ml-0.5 font-bold">
                                {ledgerSortField === "debit" ? (ledgerSortDir === "desc" ? "High→Low" : "Low→High") : ""}
                              </span>
                            </button>

                            {/* SEARCH INPUT */}
                            <div className="relative w-44 sm:w-56">
                              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                              <input
                                type="text"
                                placeholder="Search narration..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-400"
                              />
                            </div>
                          </div>
                        </div>

                        {/* ACTIVE FILTER PILL */}
                        {ledgerCategoryFilter !== "all" && (
                          <div className="flex items-center justify-between px-3.5 py-2 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-900">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-blue-700">Category Filter:</span>
                              <span className="font-bold bg-white px-2 py-0.5 rounded border border-blue-200 text-blue-950">
                                {ledgerCategoryFilter}
                              </span>
                              <span className="text-blue-700">
                                • {txs.length} transactions totaling <strong className="text-blue-950">₹{filteredTotalDebit.toLocaleString()}</strong>
                              </span>
                            </div>
                            <button
                              onClick={() => setLedgerCategoryFilter("all")}
                              className="text-xs font-semibold text-blue-700 hover:text-blue-950 flex items-center space-x-1 cursor-pointer bg-blue-100/60 hover:bg-blue-100 px-2 py-1 rounded transition"
                            >
                              <X className="w-3.5 h-3.5" />
                              <span>Clear Filter</span>
                            </button>
                          </div>
                        )}

                        {/* TRANSACTIONS TABLE */}
                        <div className="overflow-x-auto rounded-lg border border-slate-200">
                          <table className="w-full min-w-[640px] text-left text-xs">
                            <thead className="bg-slate-50 text-slate-500 font-medium text-[11px] border-b border-slate-200 select-none">
                              <tr>
                                <th
                                  onClick={() => toggleSort("date")}
                                  className="py-2.5 px-3 cursor-pointer hover:bg-slate-100 transition"
                                >
                                  <div className="flex items-center space-x-1">
                                    <span>Date</span>
                                    {ledgerSortField === "date" ? (
                                      <span className="text-slate-900 font-bold">{ledgerSortDir === "desc" ? "↓" : "↑"}</span>
                                    ) : (
                                      <ArrowUpDown className="w-3 h-3 text-slate-300" />
                                    )}
                                  </div>
                                </th>
                                <th className="py-2.5 px-3">Narration</th>
                                <th
                                  onClick={() => toggleSort("category")}
                                  className="py-2.5 px-3 cursor-pointer hover:bg-slate-100 transition"
                                >
                                  <div className="flex items-center space-x-1">
                                    <span>Category</span>
                                    {ledgerSortField === "category" ? (
                                      <span className="text-slate-900 font-bold">{ledgerSortDir === "asc" ? "A→Z" : "Z→A"}</span>
                                    ) : (
                                      <ArrowUpDown className="w-3 h-3 text-slate-300" />
                                    )}
                                  </div>
                                </th>
                                <th className="py-2.5 px-3">Mode</th>
                                <th
                                  onClick={() => toggleSort("debit")}
                                  className="py-2.5 px-3 text-right cursor-pointer hover:bg-slate-100 transition"
                                >
                                  <div className="flex items-center justify-end space-x-1">
                                    <span>Debit</span>
                                    {ledgerSortField === "debit" ? (
                                      <span className="text-slate-900 font-bold">{ledgerSortDir === "desc" ? "↓" : "↑"}</span>
                                    ) : (
                                      <ArrowUpDown className="w-3 h-3 text-slate-300" />
                                    )}
                                  </div>
                                </th>
                                <th className="py-2.5 px-3 text-right">Credit</th>
                                <th className="py-2.5 px-3 text-right">Balance</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 font-normal">
                              {txs.map((t: any, i: number) => (
                                <tr key={i} className="hover:bg-slate-50 transition">
                                  <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">{t.date}</td>
                                  <td className="py-2.5 px-3 text-slate-800 max-w-sm truncate" title={t.narration}>
                                    {t.narration}
                                  </td>
                                  <td className="py-2.5 px-3 whitespace-nowrap">
                                    <button
                                      onClick={() => setLedgerCategoryFilter(t.sub_category)}
                                      title={`Filter by ${t.sub_category}`}
                                      className={`px-2 py-0.5 rounded text-[11px] font-medium border text-left cursor-pointer transition hover:opacity-80 ${
                                        t.credit > 0 || t.category === "Income"
                                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                          : t.category === "Transfers & P2P"
                                          ? "bg-amber-50 text-amber-700 border-amber-200"
                                          : t.category === "Fixed Expenses"
                                          ? "bg-purple-50 text-purple-700 border-purple-200"
                                          : t.category === "Discretionary"
                                          ? "bg-blue-50 text-blue-700 border-blue-200"
                                          : "bg-slate-100 text-slate-700 border-slate-200"
                                      }`}
                                    >
                                      {t.sub_category}
                                    </button>
                                  </td>
                                  <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">{t.mode}</td>
                                  <td className="py-2.5 px-3 text-right font-semibold text-rose-600 whitespace-nowrap">
                                    {t.debit > 0 ? `₹${Number(t.debit).toLocaleString()}` : "-"}
                                  </td>
                                  <td className="py-2.5 px-3 text-right font-semibold text-emerald-600 whitespace-nowrap">
                                    {t.credit > 0 ? `₹${Number(t.credit).toLocaleString()}` : "-"}
                                  </td>
                                  <td className="py-2.5 px-3 text-right text-slate-600 font-medium whitespace-nowrap">
                                    {t.balance !== undefined && t.balance !== null ? `₹${Number(t.balance).toLocaleString()}` : "-"}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        {txs.length === 0 && (
                          <div className="py-8 text-center text-xs text-slate-400">
                            No transactions found matching your filter or search.
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: STATEMENT VAULT */}
          {activeTab === "statements" && (
            <div className="space-y-6">
              {/* HEADER WITH SUMMARY & CLEAR ALL BUTTON */}
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center space-x-2.5">
                  <h2 className="text-xl font-bold text-slate-900">Statements</h2>
                  <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-bold">
                    {statementsInfo?.statements?.length || 0}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs">
                    <span className="font-semibold text-slate-800">
                      {statementsInfo?.total_rows || 0}
                    </span>
                    <span>Records Ingested</span>
                  </div>

                  <button
                    onClick={handleClearStatement}
                    className="text-xs font-semibold px-2.5 sm:px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition flex items-center space-x-1.5 shadow-xs cursor-pointer shrink-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Unload All Statements</span>
                    <span className="sm:hidden">Unload All</span>
                  </button>
                </div>
              </div>

              {/* LIST OF UPLOADED STATEMENTS AS ROWS */}
              <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-3.5 sm:p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-2 bg-slate-50/70">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-slate-700 shrink-0" />
                    <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Active Ingested Statements ({statementsInfo?.statements?.length || 0})
                    </span>
                  </div>
                  <div className="text-[11px] sm:text-xs text-slate-500">
                    Unified Range: <span className="font-semibold text-slate-800">{statementsInfo?.date_range || "N/A"}</span>
                  </div>
                </div>

                {statementsInfo?.statements && statementsInfo.statements.length > 0 ? (
                  <div className="divide-y divide-slate-100">
                    {statementsInfo.statements.map((stmt: any) => (
                      <div
                        key={stmt.id}
                        className="p-3.5 sm:p-4 hover:bg-slate-50/60 transition space-y-3"
                      >
                        {/* Top Row: File icon, Filename, Upload date, and Unload Button */}
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center space-x-3 min-w-0">
                            <div className="w-9 h-9 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center shrink-0">
                              <FileText className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center space-x-2">
                                <p className="text-xs font-bold text-slate-900 truncate">
                                  {stmt.filename}
                                </p>
                                {stmt.is_demo && (
                                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 shrink-0">
                                    Demo
                                  </span>
                                )}
                              </div>
                              <p className="text-[11px] text-slate-400 mt-0.5">
                                Uploaded {stmt.uploaded_at}
                              </p>
                            </div>
                          </div>

                          <button
                            onClick={() => handleUnloadSingleStatement(stmt.id, stmt.filename)}
                            className="px-2.5 py-1 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-semibold border border-rose-200 transition flex items-center space-x-1 cursor-pointer shrink-0 shadow-2xs"
                            title={`Unload ${stmt.filename}`}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Unload</span>
                          </button>
                        </div>

                        {/* Bottom Row: Clean Structured Data Ribbon */}
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 sm:gap-4 pt-2.5 border-t border-slate-100 text-xs">
                          {/* Statement Period */}
                          <div>
                            <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
                              Period
                            </span>
                            <span className="font-semibold text-slate-800 text-[11px] sm:text-xs">
                              {stmt.date_range}
                            </span>
                          </div>

                          {/* Transactions Volume */}
                          <div>
                            <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
                              Volume
                            </span>
                            <span className="font-semibold text-slate-800 text-[11px] sm:text-xs">
                              {stmt.transactions_count} txs
                            </span>
                          </div>

                          {/* Cashflow Inflow / Outflow */}
                          <div className="col-span-2 sm:col-span-1">
                            <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
                              Cashflow In / Out
                            </span>
                            <div className="flex items-center space-x-1.5 text-[11px] sm:text-xs font-semibold">
                              <span className="text-emerald-600">+₹{Number(stmt.inflow || 0).toLocaleString()}</span>
                              <span className="text-slate-300">/</span>
                              <span className="text-slate-800">-₹{Number(stmt.outflow || 0).toLocaleString()}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-slate-400">
                    No active statements loaded in vault.
                  </div>
                )}
              </div>

              {/* UPLOAD MORE STATEMENTS AREA BELOW LIST */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`p-5 sm:p-8 rounded-xl bg-white border-2 border-dashed transition flex flex-col items-center justify-center text-center space-y-3 shadow-sm ${
                  isDragging
                    ? "border-slate-900 bg-slate-50 ring-4 ring-slate-900/5"
                    : "border-slate-300 hover:border-slate-400"
                }`}
              >
                <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
                  <Upload className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Upload More Statements</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Drag & drop or select new monthly, quarterly, or yearly statements. The system will automatically stitch them into your ledger and eliminate duplicate transactions.
                  </p>
                </div>

                <label className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold cursor-pointer transition shadow-sm">
                  <span>{uploading ? "Analyzing & Stitching..." : "Select Files to Append"}</span>
                  <input
                    type="file"
                    accept=".pdf,.csv,.xlsx,.xls"
                    multiple
                    onChange={handleFileUpload}
                    className="hidden"
                    disabled={uploading}
                  />
                </label>
              </div>
            </div>
          )}

          {/* TAB 4: MERCHANT INTELLIGENCE & DICTIONARY */}
          {activeTab === "merchants" && (
            <div className="space-y-6">
              {/* HEADER WITH SUMMARY & APPROVE ALL BUTTON */}
              <div className="flex items-center justify-between gap-2.5 sm:gap-4">
                <div className="flex items-center space-x-2.5 min-w-0">
                  <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 truncate">Merchant Intel.</h2>
                </div>

                <div className="flex items-center space-x-1.5 sm:space-x-2.5 shrink-0">
                  {merchantStats.pending_review > 0 && (
                    <button
                      onClick={handleApproveAllMerchants}
                      className="hidden sm:inline-flex whitespace-nowrap shrink-0 px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition items-center space-x-1.5 shadow-xs cursor-pointer"
                    >
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                      <span>Approve All Pending ({merchantStats.pending_review})</span>
                    </button>
                  )}
                  <button
                    onClick={handleResetMerchantCache}
                    className="whitespace-nowrap shrink-0 px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded-lg border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-semibold transition flex items-center space-x-1.5 shadow-xs cursor-pointer"
                    title="Clear all cached merchant classifications and re-run Gemini AI"
                  >
                    <Trash2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0" />
                    <span>Reset Cache & Re-run AI</span>
                  </button>

                  <button
                    onClick={fetchMerchantData}
                    className="p-1.5 sm:p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition shadow-xs cursor-pointer shrink-0"
                    title="Refresh Directory"
                  >
                    <RefreshCcw className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                  </button>
                </div>
              </div>

              {/* STATS STRIP */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                  <span className="text-xs font-medium text-slate-500">Learned Merchants</span>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{merchantStats.total}</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                  <span className="text-xs font-medium text-slate-500">Auto-Verified & Rules</span>
                  <p className="text-2xl font-bold text-emerald-600 mt-1">{merchantStats.verified}</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                  <span className="text-xs font-medium text-slate-500">Needs Review (&lt;50% Conf)</span>
                  <p className="text-2xl font-bold text-amber-600 mt-1">{merchantStats.pending_review}</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                  <span className="text-xs font-medium text-slate-500">Classification Engine</span>
                  <div className="flex items-center space-x-1.5 mt-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-xs font-bold text-slate-800">Active</span>
                  </div>
                </div>
              </div>

              {/* SEARCH & FILTER TOOLBAR */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 bg-white rounded-xl border border-slate-200/80 shadow-xs">
                {/* FILTER TABS */}
                <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg w-full sm:w-auto">
                  <button
                    onClick={() => setMerchantFilter("all")}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition cursor-pointer ${
                      merchantFilter === "all"
                        ? "bg-white text-slate-900 font-semibold shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    All ({merchantItems.length})
                  </button>

                  <button
                    onClick={() => setMerchantFilter("pending")}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition cursor-pointer flex items-center space-x-1.5 ${
                      merchantFilter === "pending"
                        ? "bg-white text-amber-900 font-semibold shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    <span>Needs Review</span>
                    {merchantStats.pending_review > 0 && (
                      <span className="px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-amber-100 text-amber-800">
                        {merchantStats.pending_review}
                      </span>
                    )}
                  </button>

                  <button
                    onClick={() => setMerchantFilter("verified")}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition cursor-pointer ${
                      merchantFilter === "verified"
                        ? "bg-white text-emerald-900 font-semibold shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Grouped by Category ({merchantStats.verified})
                  </button>
                </div>

                {/* SEARCH INPUT */}
                <div className="relative w-full sm:w-72">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search merchant, category, or UPI handle..."
                    value={merchantSearch}
                    onChange={(e) => setMerchantSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:bg-white transition"
                  />
                </div>
              </div>

              {/* RENDER LOGIC: SPLIT FILTERED LIST */}
              {(() => {
                const filtered = merchantItems.filter((m) => {
                  if (!merchantSearch) return true;
                  const s = merchantSearch.toLowerCase();
                  return (
                    m.merchant_key.toLowerCase().includes(s) ||
                    m.display_name.toLowerCase().includes(s) ||
                    m.sub_category.toLowerCase().includes(s) ||
                    (m.sample_narration && m.sample_narration.toLowerCase().includes(s))
                  );
                });

                const pendingList = filtered.filter((m) => m.needs_review || !m.verified);
                const verifiedList = filtered.filter((m) => m.verified && !m.needs_review);

                // Group verified items by sub_category
                const categoryGroupsMap: Record<string, any[]> = {};
                verifiedList.forEach((m) => {
                  const sub = m.sub_category || "Local Shopping & Services";
                  if (!categoryGroupsMap[sub]) categoryGroupsMap[sub] = [];
                  categoryGroupsMap[sub].push(m);
                });

                // Sort: groups with the most merchants first
                const sortedSubCategories = Object.keys(categoryGroupsMap).sort(
                  (a, b) => categoryGroupsMap[b].length - categoryGroupsMap[a].length
                );

                const getCategoryStyle = (sub: string) => {
                  switch (sub) {
                    case "Food Delivery & Dining":
                      return { dot: "bg-teal-500", badge: "bg-teal-50 text-teal-700 border-teal-200" };
                    case "Groceries & Supplies":
                      return { dot: "bg-emerald-500", badge: "bg-emerald-50 text-emerald-700 border-emerald-200" };
                    case "Shopping & E-Commerce":
                      return { dot: "bg-blue-500", badge: "bg-blue-50 text-blue-700 border-blue-200" };
                    case "Transfer to Friends & Contacts":
                      return { dot: "bg-amber-500", badge: "bg-amber-50 text-amber-700 border-amber-200" };
                    case "Education & Academic":
                      return { dot: "bg-indigo-500", badge: "bg-indigo-50 text-indigo-700 border-indigo-200" };
                    case "Healthcare & Eyewear":
                      return { dot: "bg-rose-500", badge: "bg-rose-50 text-rose-700 border-rose-200" };
                    case "Cloud & Tech Tools":
                    case "Subscriptions":
                      return { dot: "bg-purple-500", badge: "bg-purple-50 text-purple-700 border-purple-200" };
                    case "Utilities & Bills":
                      return { dot: "bg-orange-500", badge: "bg-orange-50 text-orange-700 border-orange-200" };
                    default:
                      return { dot: "bg-slate-500", badge: "bg-slate-50 text-slate-700 border-slate-200" };
                  }
                };

                return (
                  <div className="space-y-6">
                    {/* 1. NEEDS REVIEW SECTION */}
                    {(merchantFilter === "all" || merchantFilter === "pending") && pendingList.length > 0 && (
                      <div className="bg-amber-50/40 rounded-xl border border-amber-200/80 shadow-xs overflow-hidden">
                        <div className="px-5 py-3.5 bg-amber-50/90 border-b border-amber-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="flex items-center space-x-2.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
                            <div>
                              <div className="flex items-center space-x-2">
                                <h3 className="font-bold text-slate-900 text-xs sm:text-sm">Needs Your Review</h3>
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                                  {pendingList.length} items
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-500 mt-0.5">
                                Gemini assigned low confidence (&lt;50%) for these merchants. Confirm or change their category below.
                              </p>
                            </div>
                          </div>

                          <button
                            onClick={handleApproveAllMerchants}
                            className="whitespace-nowrap shrink-0 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition flex items-center space-x-2 shadow-xs cursor-pointer"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                            <span>Approve All ({pendingList.length})</span>
                          </button>
                        </div>

                        <div className="overflow-x-auto bg-white">
                          <table className="w-full min-w-[720px] text-left border-collapse text-xs">
                            <thead>
                              <tr className="border-b border-slate-100 text-slate-400 font-medium text-[11px] bg-slate-50/50">
                                <th className="py-2.5 px-4">Merchant & UPI Handle</th>
                                <th className="py-2.5 px-4 min-w-[200px] w-56">Category (Change to move)</th>
                                <th className="py-2.5 px-4">Confidence & AI Reasoning</th>
                                <th className="py-2.5 px-4 w-28 text-right">Action</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 font-normal">
                              {pendingList.map((m) => {
                                const isUpdating = isUpdatingMerchant === m.merchant_key;
                                return (
                                  <tr key={m.merchant_key} className="hover:bg-amber-50/20 transition">
                                    <td className="py-2.5 px-4 max-w-xs">
                                      <div className="font-semibold text-slate-900">{m.display_name}</div>
                                      {m.sample_narration && (
                                        <div
                                          className="text-[10px] text-slate-400 truncate mt-0.5 max-w-sm"
                                          title={m.sample_narration}
                                        >
                                          {m.sample_narration}
                                        </div>
                                      )}
                                    </td>

                                    <td className="py-2.5 px-4 min-w-[200px]">
                                      <select
                                        disabled={isUpdating}
                                        value={m.sub_category}
                                        onChange={(e) => handleUpdateMerchantCategory(m.merchant_key, e.target.value)}
                                        className="w-full min-w-[180px] px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs font-medium bg-white text-slate-800 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900/10 transition cursor-pointer"
                                      >
                                        {MACRO_GROUPS.map((grp) => (
                                          <optgroup key={grp.name} label={`── ${grp.name} ──`}>
                                            {grp.items.map((sub) => (
                                              <option key={sub} value={sub}>
                                                {sub}
                                              </option>
                                            ))}
                                          </optgroup>
                                        ))}
                                      </select>
                                    </td>

                                    <td className="py-2.5 px-4 max-w-md">
                                      <div className="flex items-center space-x-2">
                                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 shrink-0">
                                          {Math.round(m.confidence * 100)}%
                                        </span>
                                        <span className="text-[11px] text-slate-600 line-clamp-1" title={m.reasoning}>
                                          {m.reasoning || "Pending confirmation"}
                                        </span>
                                      </div>
                                    </td>

                                    <td className="py-2.5 px-4 text-right whitespace-nowrap">
                                      <button
                                        disabled={isUpdating}
                                        onClick={() => handleApproveMerchant(m.merchant_key)}
                                        className="px-2.5 py-1 rounded-md bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-semibold border border-emerald-200 transition inline-flex items-center space-x-1 cursor-pointer shadow-xs"
                                      >
                                        <Check className="w-3.5 h-3.5" />
                                        <span>Approve</span>
                                      </button>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* 2. VERIFIED MERCHANTS GROUPED BY CATEGORY */}
                    {(merchantFilter === "all" || merchantFilter === "verified") && (
                      <div className="space-y-4">
                        {sortedSubCategories.map((subName) => {
                          const merchantsInSub = categoryGroupsMap[subName];
                          const macro = merchantsInSub[0]?.category || "Discretionary";
                          const style = getCategoryStyle(subName);

                          return (
                            <div
                              key={subName}
                              className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden"
                            >
                              {/* CATEGORY GROUP HEADER */}
                              <div className="px-5 py-3 bg-slate-50/70 border-b border-slate-200/80 flex items-center justify-between">
                                <div className="flex items-center space-x-2.5">
                                  <span className={`w-2.5 h-2.5 rounded-full ${style.dot}`} />
                                  <span className="font-bold text-slate-900 text-xs sm:text-sm">{subName}</span>
                                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white border border-slate-200 text-slate-600">
                                    {macro}
                                  </span>
                                </div>
                                <span className="text-xs font-medium text-slate-500">
                                  {merchantsInSub.length} {merchantsInSub.length === 1 ? "merchant" : "merchants"}
                                </span>
                              </div>

                              {/* TABLE OF MERCHANTS IN THIS CATEGORY */}
                              <div className="overflow-x-auto">
                                <table className="w-full min-w-[760px] text-left border-collapse text-xs">
                                  <thead>
                                    <tr className="border-b border-slate-100 text-slate-400 font-medium text-[11px] bg-slate-50/30">
                                      <th className="py-2.5 px-4 w-52">Merchant</th>
                                      <th className="py-2.5 px-4">Raw UPI Narration</th>
                                      <th className="py-2.5 px-4 min-w-[200px] w-64">Category (Change to move)</th>
                                      <th className="py-2.5 px-4">Confidence & AI Reasoning</th>
                                      <th className="py-2.5 px-4 w-24 text-right">Status</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-slate-100 font-normal">
                                    {merchantsInSub.map((m) => {
                                      const isUpdating = isUpdatingMerchant === m.merchant_key;
                                      return (
                                        <tr key={m.merchant_key} className="hover:bg-slate-50/70 transition">
                                          {/* MERCHANT */}
                                          <td className="py-2.5 px-4 font-semibold text-slate-900 whitespace-nowrap">
                                            {m.display_name}
                                          </td>

                                          {/* NARRATION */}
                                          <td className="py-2.5 px-4 max-w-xs">
                                            {m.sample_narration ? (
                                              <div
                                                className="text-[10px] text-slate-400 truncate max-w-sm"
                                                title={m.sample_narration}
                                              >
                                                {m.sample_narration}
                                              </div>
                                            ) : (
                                              <span className="text-slate-300">-</span>
                                            )}
                                          </td>

                                          {/* DROPDOWN - MOVING CHOSEN ITEM TO NEW CATEGORY INSTANTLY */}
                                          <td className="py-2.5 px-4 min-w-[200px]">
                                            <select
                                              disabled={isUpdating}
                                              value={m.sub_category}
                                              onChange={(e) => handleUpdateMerchantCategory(m.merchant_key, e.target.value)}
                                              className="w-full min-w-[180px] px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs font-medium bg-white text-slate-800 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900/10 transition cursor-pointer"
                                            >
                                              {MACRO_GROUPS.map((grp) => (
                                                <optgroup key={grp.name} label={`── ${grp.name} ──`}>
                                                  {grp.items.map((sub) => (
                                                    <option key={sub} value={sub}>
                                                      {sub}
                                                    </option>
                                                  ))}
                                                </optgroup>
                                              ))}
                                            </select>
                                          </td>

                                          {/* CONFIDENCE & REASONING */}
                                          <td className="py-2.5 px-4 max-w-md">
                                            <div className="flex items-center space-x-2">
                                              <span
                                                className={`px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                                                  m.confidence >= 0.8
                                                    ? "bg-emerald-100 text-emerald-800"
                                                    : m.confidence >= 0.5
                                                    ? "bg-blue-100 text-blue-800"
                                                    : "bg-slate-100 text-slate-700"
                                                }`}
                                              >
                                                {Math.round(m.confidence * 100)}%
                                              </span>
                                              <span className="text-[11px] text-slate-600 line-clamp-1" title={m.reasoning}>
                                                {m.reasoning || "Verified category"}
                                              </span>
                                            </div>
                                          </td>

                                          {/* STATUS BADGE */}
                                          <td className="py-2.5 px-4 text-right whitespace-nowrap">
                                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                              <Check className="w-3 h-3" />
                                              <span>Verified</span>
                                            </span>
                                          </td>
                                        </tr>
                                      );
                                    })}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* EMPTY SEARCH STATE */}
                    {filtered.length === 0 && (
                      <div className="p-12 text-center bg-white rounded-xl border border-slate-200/80 shadow-xs">
                        <Search className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                        <p className="text-xs font-semibold text-slate-700">No merchants found</p>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          No merchants match "{merchantSearch}". Try clearing your search term.
                        </p>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          {/* TAB: FINNEAS AI FIDUCIARY CHAT */}
          {activeTab === "finneas" && (
            <div className="h-[calc(100vh-140px)] min-h-[580px] flex rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-sm relative">
              {/* MOBILE BACKDROP OVERLAY FOR THREADS SIDEBAR */}
              {showFinneasSidebar && (
                <div
                  onClick={() => setShowFinneasSidebar(false)}
                  className="fixed inset-0 bg-slate-900/40 z-40 md:hidden backdrop-blur-2xs animate-in fade-in"
                />
              )}

              {/* LEFT SIDEBAR: THREADS HISTORY (COLLAPSIBLE ON MOBILE) */}
              <div
                className={`
                  ${showFinneasSidebar ? "fixed inset-y-0 left-0 z-50 w-72 sm:w-80 bg-white shadow-2xl flex flex-col animate-in slide-in-from-left duration-200" : "hidden"}
                  md:relative md:flex md:w-72 lg:w-80 md:shadow-none md:inset-auto md:z-auto
                  border-r border-slate-200 bg-slate-50/60 flex flex-col shrink-0
                `}
              >
                <div className="p-3.5 sm:p-4 space-y-3 flex-1 flex flex-col overflow-hidden">
                  {/* MOBILE CLOSE HEADER */}
                  <div className="flex items-center justify-between md:hidden pb-2.5 border-b border-slate-200">
                    <span className="text-xs font-bold text-slate-800">Conversations</span>
                    <button
                      onClick={() => setShowFinneasSidebar(false)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition cursor-pointer"
                      aria-label="Close conversations menu"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {/* NEW CHAT BUTTON */}
                  <button
                    onClick={() => {
                      handleCreateNewThread();
                      setShowFinneasSidebar(false);
                    }}
                    className="w-full inline-flex items-center justify-center space-x-2 px-3 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-xs transition active:scale-[0.99] cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Start New Chat</span>
                  </button>

                  {/* THREADS LIST */}
                  <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 no-scrollbar">
                    {finneasThreads.length === 0 ? (
                      <div className="p-6 text-center text-xs text-slate-400 space-y-2 mt-4">
                        <MessageSquare className="w-6 h-6 text-slate-300 mx-auto" />
                        <p className="font-medium text-slate-500">No chat history yet</p>
                        <p className="text-[10px]">Start your first conversation with Finneas!</p>
                      </div>
                    ) : (
                      finneasThreads.map((thread) => {
                        const isActive = thread.id === activeThreadId;
                        const msgCount = thread.messages?.length || 0;
                        return (
                          <div
                            key={thread.id}
                            onClick={() => {
                              selectThread(thread.id);
                              setShowFinneasSidebar(false);
                            }}
                            className={`group p-3 rounded-xl border text-xs cursor-pointer transition flex items-start justify-between gap-2 ${
                              isActive
                                ? "bg-white border-purple-300 shadow-xs text-slate-900"
                                : "bg-white/60 border-slate-200/70 hover:bg-white hover:border-slate-300 text-slate-700"
                            }`}
                          >
                            <div className="flex items-start space-x-2.5 min-w-0 flex-1">
                              <MessageSquare
                                className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${
                                  isActive ? "text-purple-600" : "text-slate-400 group-hover:text-slate-600"
                                }`}
                              />
                              <div className="min-w-0 flex-1">
                                <h4 className="font-semibold truncate leading-tight text-xs">
                                  {thread.title || "Financial Discussion"}
                                </h4>
                                <div className="flex items-center space-x-2 mt-1 text-[10px] text-slate-400 font-medium">
                                  <span>{msgCount} {msgCount === 1 ? 'msg' : 'msgs'}</span>
                                  <span>•</span>
                                  <span>
                                    {new Date(thread.created_at).toLocaleDateString("en-IN", {
                                      month: "short",
                                      day: "numeric",
                                    })}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <button
                              onClick={(e) => handleDeleteThread(thread.id, e)}
                              className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-600 transition rounded"
                              title="Delete thread"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>

              {/* RIGHT MAIN CHAT ARENA */}
              <div className="flex-1 flex flex-col justify-between bg-white overflow-hidden min-w-0">
                {/* CHAT ARENA HEADER */}
                <div className="px-3.5 sm:px-6 py-3 border-b border-slate-200/80 bg-white flex items-center justify-between shrink-0 gap-2">
                  <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
                    {/* MOBILE HAMBURGER BUTTON TO TOGGLE THREADS DRAWER */}
                    <button
                      onClick={() => setShowFinneasSidebar(!showFinneasSidebar)}
                      className="md:hidden p-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 transition shrink-0 cursor-pointer"
                      title="Open conversation threads"
                    >
                      <Menu className="w-4 h-4" />
                    </button>

                    <FinneasMascot size="sm" state={finneasLoading ? "thinking" : "idle"} />
                    <div className="min-w-0">
                      <div className="flex items-center space-x-2 min-w-0">
                        <h3 className="text-xs sm:text-sm font-bold text-slate-900 truncate">
                          {activeThreadId
                            ? finneasThreads.find((t) => t.id === activeThreadId)?.title || "Financial Discussion"
                            : "Finneas Fiduciary Chat"}
                        </h3>
                        <span className="text-[10px] font-bold px-1.5 sm:px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 shrink-0">
                          AI
                        </span>
                      </div>
                      <p className="text-[10px] sm:text-[11px] text-slate-500 flex items-center space-x-1.5 truncate">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block shrink-0"></span>
                        <span className="truncate">Connected to your ledger transactions</span>
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={handleCreateNewThread}
                    className="inline-flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition cursor-pointer shrink-0"
                  >
                    <Plus className="w-3.5 h-3.5 text-slate-500" />
                    <span className="hidden sm:inline">New Thread</span>
                  </button>
                </div>

                {/* CHAT MESSAGES STREAM */}
                <div className="flex-1 overflow-y-auto p-3.5 sm:p-6 space-y-4 sm:space-y-6">
                  {finneasMessages.length === 0 ? (
                    /* EMPTY STATE HERO (COMPACT & WIDE SO SUGGESTIONS STAY IN ONE LINE) */
                    <div className="max-w-4xl mx-auto py-1 sm:py-4 text-center space-y-2 sm:space-y-3.5">
                      <div className="flex flex-col items-center">
                        <FinneasMascot size="xl" state="idle" variant="welcome" />
                        <div className="mt-1 sm:mt-2 px-3 py-1.5 sm:py-2 sm:px-4 rounded-xl sm:rounded-2xl bg-purple-50/70 border border-purple-200 text-slate-800 text-center max-w-md shadow-xs">
                          <p className="text-xs sm:text-sm font-semibold text-purple-950">
                            "Hi, I'm <strong className="font-extrabold text-purple-900">Finn-eas</strong>! I make finance easy for you."
                          </p>
                        </div>
                      </div>

                      {/* STARTER PROMPT CHIPS */}
                      <div className="space-y-1 sm:space-y-1.5">
                        <span className="text-[10px] sm:text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                          Suggested Questions to Try
                        </span>
                        <div className="grid grid-cols-2 gap-1.5 sm:gap-2.5 text-left">
                          {[
                            {
                              icon: <Utensils className="w-3.5 h-3.5 text-purple-600 shrink-0" />,
                              title: "Food & Dining Trends",
                              prompt: "What are the trends of my food expenses?",
                            },
                            {
                              icon: <Store className="w-3.5 h-3.5 text-indigo-600 shrink-0" />,
                              title: "Merchant Spend Lookup",
                              prompt: "How much have I spent on McDonald's or food delivery recently?",
                            },
                            {
                              icon: <CreditCard className="w-3.5 h-3.5 text-emerald-600 shrink-0" />,
                              title: "Loan Affordability Audit",
                              prompt: "Can I afford a personal loan with an EMI of ₹10,000/mo?",
                            },
                            {
                              icon: <ShieldCheck className="w-3.5 h-3.5 text-blue-600 shrink-0" />,
                              title: "Insurance Protection Gap",
                              prompt: "What is my current insurance protection deficit and HLV gap?",
                            },
                            {
                              icon: <Target className="w-3.5 h-3.5 text-amber-600 shrink-0" />,
                              title: "Goal Savings Feasibility",
                              prompt: "Can I save ₹1 Lakh over the next 12 months with my current surplus?",
                            },
                            {
                              icon: <Repeat className="w-3.5 h-3.5 text-violet-600 shrink-0" />,
                              title: "Subscriptions Audit",
                              prompt: "What recurring subscriptions and services am I paying for?",
                            },
                          ].map((chip, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSendFinneasMessage(chip.prompt)}
                              className="p-2 sm:px-3.5 sm:py-2.5 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-purple-50/50 hover:border-purple-300 transition text-left cursor-pointer group shadow-2xs space-y-0.5 sm:space-y-1"
                            >
                              <div className="flex items-center space-x-1.5 text-[11px] sm:text-xs font-bold text-slate-900 group-hover:text-purple-900 leading-tight">
                                <span>{chip.icon}</span>
                                <span className="truncate">{chip.title}</span>
                              </div>
                              <p className="hidden sm:block text-[11px] text-slate-500 whitespace-nowrap overflow-hidden text-ellipsis group-hover:text-slate-700">
                                "{chip.prompt}"
                              </p>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* MESSAGES LIST */
                    finneasMessages.map((msg, idx) => {
                      const isUser = msg.role === "user";
                      return (
                        <div
                          key={msg.id || idx}
                          className={`flex items-start space-x-3 ${isUser ? "justify-end" : "justify-start"}`}
                        >
                          {!isUser && (
                            <div className="shrink-0 mt-0.5">
                              <FinneasMascot size="sm" state="idle" />
                            </div>
                          )}

                          <div
                            className={`max-w-2xl rounded-2xl p-4 space-y-2 text-xs leading-relaxed shadow-xs ${
                              isUser
                                ? "bg-slate-900 text-white rounded-tr-xs"
                                : "bg-white border border-slate-200/90 text-slate-800 rounded-tl-xs"
                            }`}
                          >
                            {/* EXECUTED TOOLS PILLS (IF ASSISTANT) */}
                            {!isUser && msg.executed_tools && msg.executed_tools.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 pb-2 border-b border-slate-100">
                                {msg.executed_tools.map((t: any, tIdx: number) => (
                                  <span
                                    key={tIdx}
                                    className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-50 text-slate-700 border border-slate-200 text-[10px] font-semibold"
                                  >
                                    <Zap className="w-3 h-3 text-purple-600 shrink-0" />
                                    <span>{(t.summary || t.tool_name).replace("in None months", "within 12 months")}</span>
                                  </span>
                                ))}
                              </div>
                            )}

                            {/* ATTACHMENTS (IF USER MESSAGE HAS THEM) */}
                            {msg.attachments && msg.attachments.length > 0 && (
                              <div className="flex flex-wrap gap-2 pt-1 pb-1">
                                {msg.attachments.map((att: any, attIdx: number) => {
                                  const isImg =
                                    att.type?.startsWith("image/") ||
                                    att.name?.match(/\.(png|jpg|jpeg|webp)$/i);
                                  const targetUrl = att.previewUrl || (att.url ? `${API_BASE}${att.url}` : null);

                                  return (
                                    <div
                                      key={att.id || attIdx}
                                      className={`flex items-center space-x-2 px-2.5 py-1.5 rounded-xl border text-[11px] ${
                                        isUser
                                          ? "bg-slate-800 border-slate-700 text-slate-100"
                                          : "bg-slate-50 border-slate-200 text-slate-800"
                                      }`}
                                    >
                                      {isImg ? (
                                        <ImageIcon className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                                      ) : (
                                        <FileText className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                                      )}
                                      <span
                                        className="font-semibold truncate max-w-[130px] sm:max-w-[200px]"
                                        title={att.name}
                                      >
                                        {att.name}
                                      </span>
                                      {att.size > 0 && (
                                        <span
                                          className={`text-[10px] ${
                                            isUser ? "text-slate-400" : "text-slate-500"
                                          }`}
                                        >
                                          ({(att.size / 1024).toFixed(0)} KB)
                                        </span>
                                      )}
                                      {targetUrl && (
                                        <a
                                          href={targetUrl}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className={`p-0.5 rounded transition ${
                                            isUser
                                              ? "text-slate-400 hover:text-white"
                                              : "text-slate-500 hover:text-slate-900"
                                          }`}
                                          title="Open document"
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                        </a>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            )}

                            {/* MESSAGE TEXT CONTENT */}
                            {isUser ? (
                              <p className="whitespace-pre-wrap font-medium">{msg.content}</p>
                            ) : (
                              <FinneasMessageContent content={msg.content} />
                            )}

                            {/* TIMESTAMP */}
                            <div className="text-[10px] pt-1 text-right text-slate-400 font-medium">
                              {msg.timestamp
                                ? new Date(msg.timestamp).toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  })
                                : ""}
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}

                  {/* LOADING THINKING INDICATOR */}
                  {finneasLoading && (
                    <div className="flex items-start space-x-3 justify-start">
                      <div className="shrink-0 mt-0.5">
                        <FinneasMascot size="sm" state="thinking" />
                      </div>
                      <div className="p-3.5 rounded-2xl rounded-tl-xs bg-slate-50 border border-slate-200 text-slate-600 text-xs flex items-center space-x-2.5 shadow-xs">
                        <RefreshCcw className="w-3.5 h-3.5 animate-spin text-purple-600" />
                        <span className="font-medium text-slate-700">
                          {finneasMessages.length > 0 &&
                          finneasMessages[finneasMessages.length - 1]?.attachments?.length > 0
                            ? "Finn-eas is auditing your attached document(s) & extracting fine print..."
                            : "Finn-eas is querying your statement ledger & analyzing cashflow..."}
                        </span>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* BOTTOM CHAT INPUT BAR */}
                <div className="p-4 border-t border-slate-200 bg-slate-50/50 shrink-0">
                  {/* PENDING ATTACHMENTS PREVIEW CHIPS */}
                  {finneasAttachments.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2.5 px-0.5">
                      {finneasAttachments.map((att, idx) => {
                        const isImg = att.type.startsWith("image/");
                        return (
                          <div
                            key={idx}
                            className="flex items-center space-x-2 bg-white border border-purple-200 text-slate-800 rounded-lg px-2.5 py-1.5 text-xs shadow-2xs group animate-in fade-in"
                          >
                            {isImg ? (
                              <ImageIcon className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                            ) : (
                              <FileText className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                            )}
                            <span className="font-semibold max-w-[140px] truncate" title={att.name}>
                              {att.name}
                            </span>
                            <span className="text-[10px] text-slate-400">
                              ({(att.size / 1024).toFixed(0)} KB)
                            </span>
                            <button
                              type="button"
                              onClick={() => handleRemoveAttachment(idx)}
                              className="text-slate-400 hover:text-rose-600 p-0.5 rounded transition cursor-pointer"
                              title="Remove attachment"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendFinneasMessage();
                    }}
                    className="flex items-center space-x-2 bg-white rounded-xl border border-slate-300 p-1.5 shadow-xs focus-within:ring-2 focus-within:ring-purple-600/20 focus-within:border-purple-600 transition"
                  >
                    {/* HIDDEN FILE INPUT */}
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept="application/pdf,image/png,image/jpeg,image/webp"
                      className="hidden"
                      onChange={handleFileSelect}
                    />

                    {/* ATTACHMENT PLUS BUTTON */}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={finneasLoading}
                      className="inline-flex items-center justify-center p-2 rounded-lg text-slate-500 hover:text-purple-700 hover:bg-purple-50 transition cursor-pointer disabled:opacity-40"
                      title="Attach policy brochure, quote PDF, or screenshot (+)"
                    >
                      <Plus className="w-4 h-4" />
                    </button>

                    <input
                      type="text"
                      value={finneasInput}
                      onChange={(e) => setFinneasInput(e.target.value)}
                      placeholder={
                        finneasAttachments.length > 0
                          ? "Ask Finneas to audit, compare, or explain this document..."
                          : "Ask Finn-eas about spending, loan affordability, or attach policies to compare (+)..."
                      }
                      className="flex-1 px-2 py-2 text-xs text-slate-900 bg-transparent placeholder:text-slate-400 focus:outline-none"
                    />

                    <button
                      type="submit"
                      disabled={(!finneasInput.trim() && finneasAttachments.length === 0) || finneasLoading}
                      className="inline-flex items-center justify-center p-2 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white transition cursor-pointer"
                      title="Send message"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </form>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ADD DECLARED POLICY MODAL */}
      {showAddPolicyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-slate-900" />
                <h3 className="text-base font-bold text-slate-900">Declare Off-Statement Policy</h3>
              </div>
              <button
                onClick={() => setShowAddPolicyModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddPolicySubmit} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Policy Category</label>
                  <select
                    value={addPolicyForm.category}
                    onChange={(e) => setAddPolicyForm({ ...addPolicyForm, category: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-800 text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-slate-900"
                  >
                    <option value="HEALTH">Health Insurance</option>
                    <option value="LIFE">Life Insurance (Term)</option>
                    <option value="MOTOR">Motor / Vehicle Insurance</option>
                    <option value="PERSONAL_ACCIDENT">Personal Accident Cover</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Policy Source</label>
                  <select
                    value={addPolicyForm.source}
                    onChange={(e) =>
                      setAddPolicyForm({
                        ...addPolicyForm,
                        source: e.target.value,
                        is_employer_provided: e.target.value === "EMPLOYER_GMC",
                      })
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-800 text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-slate-900"
                  >
                    <option value="EMPLOYER_GMC">Employer Corporate GMC</option>
                    <option value="PERSONAL_RETAIL">Personal Retail Policy</option>
                    <option value="FAMILY_POLICY">Family Policy (Paid by Parent/Spouse)</option>
                    <option value="OTHER_ACCOUNT">Paid from Other Bank Account</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Insurance Company / Provider</label>
                <input
                  type="text"
                  placeholder="e.g. HDFC ERGO, Star Health, Max Life, Care"
                  value={addPolicyForm.insurer_name}
                  onChange={(e) => setAddPolicyForm({ ...addPolicyForm, insurer_name: e.target.value })}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-800 text-xs focus:outline-hidden focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Plan / Product Name</label>
                <input
                  type="text"
                  placeholder="e.g. Optima Secure, Smart Total Elite, Corporate Floater"
                  value={addPolicyForm.plan_name}
                  onChange={(e) => setAddPolicyForm({ ...addPolicyForm, plan_name: e.target.value })}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-800 text-xs focus:outline-hidden focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Sum Insured / Cover (₹)</label>
                  <input
                    type="number"
                    min="50000"
                    step="50000"
                    placeholder="e.g. 1000000"
                    value={addPolicyForm.sum_insured}
                    onChange={(e) => setAddPolicyForm({ ...addPolicyForm, sum_insured: Number(e.target.value) })}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-800 text-xs focus:outline-hidden focus:ring-2 focus:ring-slate-900"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Annual Premium (₹)</label>
                  <input
                    type="number"
                    min="0"
                    step="500"
                    placeholder="0 if employer sponsored"
                    value={addPolicyForm.annual_premium}
                    onChange={(e) => setAddPolicyForm({ ...addPolicyForm, annual_premium: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-800 text-xs focus:outline-hidden focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Covered Members</label>
                <input
                  type="text"
                  placeholder="e.g. Self, Spouse, 1 Child (comma separated)"
                  value={addPolicyForm.covered_members}
                  onChange={(e) => setAddPolicyForm({ ...addPolicyForm, covered_members: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-800 text-xs focus:outline-hidden focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="roomRentCap"
                  checked={addPolicyForm.has_room_rent_capping}
                  onChange={(e) => setAddPolicyForm({ ...addPolicyForm, has_room_rent_capping: e.target.checked })}
                  className="rounded border-slate-300 text-slate-900 focus:ring-slate-900"
                />
                <label htmlFor="roomRentCap" className="text-xs text-slate-700 cursor-pointer">
                  Policy has Room Rent Capping / Sub-limit (e.g. 1% room rent clause)
                </label>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddPolicyModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold transition shadow-xs"
                >
                  Save Policy to Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* FLOATING FINNEAS TRIGGER BUTTON */}
      {activeTab !== "finneas" && hasStatement && (
        <button
          onClick={() => setActiveTab("finneas")}
          className="fixed bottom-6 right-6 z-40 flex items-center space-x-2.5 px-4 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white shadow-xl transition active:scale-95 cursor-pointer border border-slate-700 group"
          title="Open Finn-eas AI Assistant"
        >
          <FinneasMascot size="sm" state="idle" />
          <span className="text-xs font-bold tracking-tight">Ask Finn-eas</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        </button>
      )}
    </div>
  );
}
