import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { LifecycleItem, RegimeAnalysisResult, ContractSpec, NormalizationBreakdown } from "../types/api";
import { Badge } from "../components/common/Badge";
import {
  Calendar, RefreshCw, Clock, Waves, Calculator, CheckCircle2
} from "lucide-react";

export const LifecycleView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"lifecycle" | "specs" | "regimes">("lifecycle");
  const [contracts, setContracts] = useState<LifecycleItem[]>([]);
  const [rollSummary, setRollSummary] = useState("");
  const [regime, setRegime] = useState<RegimeAnalysisResult | null>(null);
  const [specs, setSpecs] = useState<ContractSpec[]>([]);
  const [calcSymbol, setCalcSymbol] = useState("GOLDM");
  const [calcPrice, setCalcPrice] = useState(75000);
  const [breakdown, setBreakdown] = useState<NormalizationBreakdown | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    runNormalization();
  }, [calcSymbol, calcPrice]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [lcRes, regRes, specRes] = await Promise.all([
        api.getLifecycle(),
        api.getRegime(),
        api.getContracts()
      ]);
      setContracts(lcRes.contracts);
      setRollSummary(lcRes.roll_schedule_summary);
      setRegime(regRes);
      setSpecs(specRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runNormalization = async () => {
    try {
      const res = await api.normalizePrice(calcSymbol, calcPrice);
      setBreakdown(res.breakdown);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <Calendar className="w-5 h-5 text-amber-600" />
            Contract Lifecycle, Expiry Radar & Specifications
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Monitor physical tender window proximity, roll transition schedules, verified MCX quotation bases, and structural break regimes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Tabs */}
          <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg text-xs font-semibold">
            <button
              onClick={() => setActiveTab("lifecycle")}
              className={`px-3 py-1.5 rounded transition ${
                activeTab === "lifecycle" ? "bg-white text-gray-900 shadow-xs" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Expiry Radar & Lifecycle
            </button>
            <button
              onClick={() => setActiveTab("specs")}
              className={`px-3 py-1.5 rounded transition ${
                activeTab === "specs" ? "bg-white text-gray-900 shadow-xs" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Contract Specifications
            </button>
            <button
              onClick={() => setActiveTab("regimes")}
              className={`px-3 py-1.5 rounded transition ${
                activeTab === "regimes" ? "bg-white text-gray-900 shadow-xs" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Regime Shifts
            </button>
          </div>

          <button
            onClick={loadData}
            className="p-1.5 border border-gray-200 rounded hover:bg-gray-50 text-gray-600"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* TAB 1: EXPIRY RADAR & LIFECYCLE */}
      {activeTab === "lifecycle" && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" /> Contract Expiry Calendar & Delivery Proximity
              </h2>
              <span className="text-xs text-gray-400 font-mono">
                {contracts.length} Monitored MCX Contracts
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-50 text-gray-600 font-medium uppercase text-[10px] tracking-wider border-b border-gray-200">
                  <tr>
                    <th className="py-2.5 px-4">Contract Symbol</th>
                    <th className="py-2.5 px-3">Expiry Date</th>
                    <th className="py-2.5 px-3">Days to Expiry</th>
                    <th className="py-2.5 px-3">Observations</th>
                    <th className="py-2.5 px-3">Data Coverage</th>
                    <th className="py-2.5 px-3">Avg Daily Volume</th>
                    <th className="py-2.5 px-3">Liquidity Status</th>
                    <th className="py-2.5 px-4">Expiry Warning Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-mono text-[11px]">
                  {contracts.map((c, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-2.5 px-4 font-bold text-gray-900 font-sans">{c.symbol}</td>
                      <td className="py-2.5 px-3 text-gray-700">{c.expiry_date}</td>
                      <td
                        className={`py-2.5 px-3 font-bold tabular-nums ${
                          c.days_to_expiry <= 3 ? "text-rose-700" : "text-gray-900"
                        }`}
                      >
                        {c.days_to_expiry} days
                      </td>
                      <td className="py-2.5 px-3 text-gray-600 tabular-nums">{c.available_observations}</td>
                      <td className="py-2.5 px-3 text-gray-600 tabular-nums">{c.data_coverage_pct}%</td>
                      <td className="py-2.5 px-3 text-gray-700 tabular-nums">
                        {c.average_daily_volume.toFixed(0)} lots
                      </td>
                      <td className="py-2.5 px-3 font-sans">
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            c.is_liquid_enough
                              ? "bg-emerald-50 text-emerald-800"
                              : "bg-amber-50 text-amber-800"
                          }`}
                        >
                          {c.is_liquid_enough ? "LIQUID" : "LOW_VOLUME"}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 font-sans">
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                            c.expiry_warning_level === "NORMAL"
                              ? "bg-gray-100 text-gray-700"
                              : c.expiry_warning_level === "CRITICAL_DELIVERY_IMMINENT"
                              ? "bg-rose-100 text-rose-800 font-bold"
                              : "bg-amber-100 text-amber-800 font-bold"
                          }`}
                        >
                          {c.expiry_warning_level.replace(/_/g, " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {rollSummary && (
            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2">
                Roll Schedule & Transition Advisory
              </h3>
              <p className="text-xs text-gray-600 font-mono leading-relaxed bg-gray-50 p-3 rounded border border-gray-100">
                {rollSummary}
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CONTRACT SPECIFICATIONS & CALCULATOR */}
      {activeTab === "specs" && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider">
                Official MCX Bullion Contract Specifications
              </h2>
              <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Official Circular Verified
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-50 text-gray-600 font-medium uppercase text-[10px] tracking-wider border-b border-gray-200">
                  <tr>
                    <th className="py-2.5 px-4">Symbol</th>
                    <th className="py-2.5 px-3">Contract Name</th>
                    <th className="py-2.5 px-3">Trading Unit</th>
                    <th className="py-2.5 px-3">Quotation Basis</th>
                    <th className="py-2.5 px-3">Gold Fineness</th>
                    <th className="py-2.5 px-3">Tick Size</th>
                    <th className="py-2.5 px-3">Delivery Unit</th>
                    <th className="py-2.5 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-mono text-[11px]">
                  {specs.map((s) => (
                    <tr key={s.symbol} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-2.5 px-4 font-bold text-gray-900 font-sans">{s.symbol}</td>
                      <td className="py-2.5 px-3 font-sans text-gray-700">{s.name}</td>
                      <td className="py-2.5 px-3 text-gray-900">{s.trading_unit_grams}g</td>
                      <td className="py-2.5 px-3 text-amber-900 font-bold">Per {s.quotation_basis_grams}g</td>
                      <td className="py-2.5 px-3 text-gray-900 font-bold">{s.purity_per_mille} / 1000</td>
                      <td className="py-2.5 px-3 text-gray-600">Rs {s.tick_size.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-gray-600">{s.delivery_unit_grams}g</td>
                      <td className="py-2.5 px-4 font-sans">
                        <Badge variant="investigate">VERIFIED</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Live Interactive Normalization Calculator */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-5 bg-white border border-gray-200 rounded-lg p-5 space-y-4">
              <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-gray-100 pb-2.5">
                <Calculator className="w-4 h-4 text-amber-600" /> Pure Gold Normalization Tool
              </h2>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-gray-600 font-medium mb-1">Contract Variant</label>
                  <select
                    value={calcSymbol}
                    onChange={(e) => setCalcSymbol(e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 rounded px-3 py-1.5 font-semibold text-gray-800"
                  >
                    {specs.map((s) => (
                      <option key={s.symbol} value={s.symbol}>
                        {s.symbol} — {s.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-gray-600 font-medium mb-1">Quoted Market Price (INR)</label>
                  <input
                    type="number"
                    value={calcPrice}
                    onChange={(e) => setCalcPrice(parseFloat(e.target.value) || 0)}
                    className="w-full bg-gray-50 border border-gray-200 rounded px-3 py-1.5 font-mono text-sm"
                  />
                  <span className="text-[10px] text-gray-400 mt-0.5 block">
                    Quoted basis: Per {specs.find((s) => s.symbol === calcSymbol)?.quotation_basis_grams} grams
                  </span>
                </div>
              </div>
            </div>

            {breakdown && (
              <div className="lg:col-span-7 bg-white border border-gray-200 rounded-lg p-5 space-y-4">
                <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider border-b border-gray-100 pb-2.5">
                  Mathematical Decomposition & Conversion Math
                </h2>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-amber-50/50 border border-amber-200/60 rounded">
                    <div className="text-[10px] font-bold text-amber-900 uppercase tracking-wider">
                      Normalized Reference Price
                    </div>
                    <div className="text-2xl font-bold font-mono text-amber-950 mt-1">
                      ₹{breakdown.normalized_pure_gold_per_gram.toFixed(2)}
                      <span className="text-xs font-sans font-normal text-amber-700 ml-1">/ pure gram</span>
                    </div>
                  </div>

                  <div className="p-3 bg-gray-50 border border-gray-200 rounded">
                    <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                      10g Pure Reference
                    </div>
                    <div className="text-2xl font-bold font-mono text-gray-900 mt-1">
                      ₹{(breakdown.normalized_pure_gold_per_gram * 10).toFixed(2)}
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-gray-50 rounded border border-gray-200 text-xs font-mono space-y-1">
                  <div className="text-gray-500 text-[10px] uppercase font-sans font-bold">Standard Formula:</div>
                  <div className="text-gray-900 font-semibold">{breakdown.formula_latex}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: REGIME SHIFTS */}
      {activeTab === "regimes" && regime && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div>
              <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
                <Waves className="w-4 h-4 text-amber-600" />
                CUSUM Structural Change & Volatility Regimes
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Detects non-stationary breaks in spread dynamics and flags periods where mean-reversion assumptions breakdown.
              </p>
            </div>
            <Badge variant="investigate">
              Current: {regime.current_regime.replace(/_/g, " ")}
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="bg-gray-50 border border-gray-100 rounded p-3 text-center">
              <div className="text-[10px] text-gray-400 font-sans">Regime Shifts Detected</div>
              <div className="text-xl font-bold text-gray-900 mt-1">
                {regime.structural_breaks_detected?.length || 0}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-100 rounded p-3 text-center">
              <div className="text-[10px] text-gray-400 font-sans">Recent Annualized Volatility</div>
              <div className="text-xl font-bold text-gray-900 mt-1">
                {regime.recent_annualized_vol_pct.toFixed(2)}%
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-100 rounded p-3 text-center">
              <div className="text-[10px] text-gray-400 font-sans">Market State</div>
              <div className="text-xl font-bold text-emerald-700 mt-1">
                {regime.volatility_clusters?.[0]?.market_state || "NORMAL_VOLATILITY"}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
