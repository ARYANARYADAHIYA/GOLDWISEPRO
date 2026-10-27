import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import type { AnomalyCandidate, ScanResponse } from "../types/api";
import { Badge } from "../components/common/Badge";
import {
  Activity, ShieldAlert, CheckCircle2, XCircle,
  FileSearch, BookmarkPlus, Play, RefreshCw
} from "lucide-react";

interface ScannerViewProps {
  onInspectAutopsy: (candidate: AnomalyCandidate) => void;
  onInspectCounterfactual: (candidate: AnomalyCandidate) => void;
  onAddToCasebook: (candidate: AnomalyCandidate) => void;
}

export const ScannerView: React.FC<ScannerViewProps> = ({
  onInspectAutopsy,
  onInspectCounterfactual,
  onAddToCasebook,
}) => {
  const [symbolA, setSymbolA] = useState("GOLDM");
  const [symbolB, setSymbolB] = useState("GOLD");
  const [zscoreThreshold, setZscoreThreshold] = useState(2.0);
  const [rollingWindow, setRollingWindow] = useState(20);
  const [slippageBps, setSlippageBps] = useState(3.0);
  const [expiryBuffer, setExpiryBuffer] = useState(3);

  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<AnomalyCandidate | null>(null);
  const [filterVerdict, setFilterVerdict] = useState<string>("ALL");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    runInitialScan();
  }, []);

  const runInitialScan = async () => {
    try {
      setLoading(true);
      setError(null);
      const health = await api.getHealth();
      const dsId = health.active_dataset_id || "ds-synthetic-mcx-gold-baseline";
      const res = await api.runScan({
        dataset_id: dsId,
        pair_symbol_a: symbolA,
        pair_symbol_b: symbolB,
        zscore_threshold: zscoreThreshold,
        rolling_window_days: rollingWindow,
        slippage_bps: slippageBps,
        expiry_buffer_days: expiryBuffer,
      });
      setScanResult(res);
      if (res.candidates.length > 0) {
        // Select first investigate candidate or first overall
        const firstInvestigate = res.candidates.find((c) => c.verdict === "INVESTIGATE");
        setSelectedCandidate(firstInvestigate || res.candidates[0]);
      }
    } catch (err: any) {
      setError(err.message || "Scan failed");
    } finally {
      setLoading(false);
    }
  };

  const filteredCandidates =
    scanResult?.candidates?.filter((c) => {
      if (filterVerdict === "ALL") return true;
      return c.verdict === filterVerdict;
    }) || [];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Scanner Control Deck */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-4 mb-4">
          <div>
            <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
              <Activity className="w-5 h-5 text-amber-600" />
              Relative Value Scanner & Opportunity Destroyer
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Strict pairwise cointegration screening backed by 12 automated falsification disproof checks.
            </p>
          </div>

          <button
            onClick={runInitialScan}
            disabled={loading}
            className="px-4 py-2 bg-gray-900 text-white rounded font-semibold text-xs hover:bg-gray-800 transition flex items-center gap-2 disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-white" />}
            Execute Scan
          </button>
        </div>

        {/* Configuration inputs */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-xs">
          <div>
            <label className="block text-gray-500 font-medium mb-1">Contract A</label>
            <select
              value={symbolA}
              onChange={(e) => setSymbolA(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-semibold text-gray-800"
            >
              <option value="GOLDM">GOLDM (100g)</option>
              <option value="GOLD">GOLD (1kg)</option>
              <option value="GOLDGUINEA">GOLDGUINEA (8g)</option>
              <option value="GOLDPETAL">GOLDPETAL (1g)</option>
              <option value="GOLDTEN">GOLDTEN (10g)</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Benchmark B</label>
            <select
              value={symbolB}
              onChange={(e) => setSymbolB(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-semibold text-gray-800"
            >
              <option value="GOLD">GOLD (1kg Benchmark)</option>
              <option value="GOLDM">GOLDM (100g)</option>
              <option value="GOLDTEN">GOLDTEN (100g)</option>
              <option value="GOLDGUINEA">GOLDGUINEA (8g)</option>
              <option value="GOLDPETAL">GOLDPETAL (1g)</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Z-Score Hurdle</label>
            <input
              type="number"
              step="0.1"
              value={zscoreThreshold}
              onChange={(e) => setZscoreThreshold(parseFloat(e.target.value) || 2.0)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-800"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Rolling Window</label>
            <input
              type="number"
              value={rollingWindow}
              onChange={(e) => setRollingWindow(parseInt(e.target.value) || 20)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-800"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Slippage (bps)</label>
            <input
              type="number"
              step="0.5"
              value={slippageBps}
              onChange={(e) => setSlippageBps(parseFloat(e.target.value) || 3.0)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-800"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Expiry Buffer (days)</label>
            <input
              type="number"
              value={expiryBuffer}
              onChange={(e) => setExpiryBuffer(parseInt(e.target.value) || 3)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-800"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded text-sm">{error}</div>
      )}

      {/* Main Grid: Candidates Table (Left) & Opportunity Destroyer Panel (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Candidates Table (7 Cols) */}
        <div className="lg:col-span-7 bg-white border border-gray-200 rounded-lg flex flex-col">
          <div className="p-3 border-b border-gray-200 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-gray-500 font-medium">Filter:</span>
              {(["ALL", "INVESTIGATE", "SUPPRESSED", "INSUFFICIENT_DATA"] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setFilterVerdict(v)}
                  className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                    filterVerdict === v
                      ? "bg-gray-900 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {v === "ALL" ? `All (${scanResult?.total_candidates || 0})` : v}
                </button>
              ))}
            </div>

            <span className="text-xs text-gray-400 font-mono">
              Showing {filteredCandidates.length} observations
            </span>
          </div>

          <div className="overflow-x-auto flex-1 max-h-[600px] overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-600 font-medium uppercase text-[10px] tracking-wider sticky top-0 border-b border-gray-200">
                <tr>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-2">Leg A / B</th>
                  <th className="py-2.5 px-2">Spread (bps)</th>
                  <th className="py-2.5 px-2">Z-Score</th>
                  <th className="py-2.5 px-2">Expiry</th>
                  <th className="py-2.5 px-3">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-mono text-[11px]">
                {filteredCandidates.map((cand) => {
                  const isSelected = selectedCandidate?.id === cand.id;
                  return (
                    <tr
                      key={cand.id}
                      onClick={() => setSelectedCandidate(cand)}
                      className={`cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-amber-50/70 border-l-4 border-amber-600"
                          : "hover:bg-gray-50/70"
                      }`}
                    >
                      <td className="py-2 px-3 text-gray-900 font-medium">{cand.timestamp}</td>
                      <td className="py-2 px-2 text-gray-700">
                        {cand.normalized_a.toFixed(1)} / {cand.normalized_b.toFixed(1)}
                      </td>
                      <td
                        className={`py-2 px-2 font-bold tabular-nums ${
                          cand.percentage_spread >= 0 ? "text-emerald-700" : "text-rose-700"
                        }`}
                      >
                        {(cand.percentage_spread * 100.0).toFixed(1)}
                      </td>
                      <td className="py-2 px-2 text-gray-800 tabular-nums">
                        {cand.robust_zscore != null ? cand.robust_zscore.toFixed(2) : "—"}
                      </td>
                      <td className="py-2 px-2 text-gray-500 font-sans text-[10px]">
                        {cand.expiry_distance_days}d
                      </td>
                      <td className="py-2 px-3 font-sans">
                        <Badge
                          variant={
                            cand.verdict === "INVESTIGATE"
                              ? "investigate"
                              : cand.verdict === "SUPPRESSED"
                              ? "suppressed"
                              : "insufficient"
                          }
                        >
                          {cand.verdict}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Opportunity Destroyer Falsification Engine (5 Cols) */}
        <div className="lg:col-span-5 bg-white border border-gray-200 rounded-lg p-5 flex flex-col justify-between space-y-4">
          {selectedCandidate ? (
            <div>
              <div className="border-b border-gray-200 pb-3 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-amber-600" />
                    <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                      Opportunity Destroyer Report
                    </h2>
                  </div>
                  <Badge
                    variant={
                      selectedCandidate.verdict === "INVESTIGATE"
                        ? "investigate"
                        : selectedCandidate.verdict === "SUPPRESSED"
                        ? "suppressed"
                        : "insufficient"
                    }
                  >
                    {selectedCandidate.verdict}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500 font-mono mt-1">
                  <span>Candidate: {selectedCandidate.id}</span>
                  <span>Observed: {selectedCandidate.timestamp}</span>
                </div>
              </div>

              {/* Spread & Friction Summary */}
              <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-4 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500 text-[10px] uppercase">Gross Spread</span>
                  <div className="text-base font-bold text-gray-900 font-mono">
                    {(selectedCandidate.percentage_spread * 100.0).toFixed(1)} bps
                  </div>
                </div>
                <div>
                  <span className="text-gray-500 text-[10px] uppercase">Estimated Friction</span>
                  <div className="text-base font-bold text-gray-600 font-mono">
                    {selectedCandidate.estimated_cost_bps.toFixed(1)} bps
                  </div>
                </div>
              </div>

              {/* 12 Disproof Checks Breakdown */}
              <div className="space-y-2 mb-4 max-h-[340px] overflow-y-auto pr-1">
                <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  12 Rigorous Falsification Tests
                </div>
                {selectedCandidate.destroyer_checks?.checks?.map((check, idx) => (
                  <div
                    key={idx}
                    className={`border rounded p-2 text-xs flex items-start gap-2 ${
                      check.passed
                        ? "bg-emerald-50/30 border-emerald-200 text-gray-800"
                        : check.severity === "FATAL_DISPROVAL"
                        ? "bg-rose-50 border-rose-200 text-rose-900"
                        : "bg-amber-50 border-amber-200 text-amber-900"
                    }`}
                  >
                    {check.passed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <div className="flex items-center justify-between font-semibold">
                        <span>{check.check_name}</span>
                        <span className="text-[10px] font-mono uppercase">{check.severity}</span>
                      </div>
                      <div className="text-[11px] text-gray-600 mt-0.5 leading-snug">
                        {check.explanation}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="pt-3 border-t border-gray-200 flex flex-wrap items-center gap-2">
                <button
                  onClick={() => onInspectAutopsy(selectedCandidate)}
                  className="flex-1 px-3 py-1.5 bg-gray-900 text-white rounded text-xs font-semibold hover:bg-gray-800 transition flex items-center justify-center gap-1.5"
                >
                  <FileSearch className="w-3.5 h-3.5 text-amber-400" /> Signal Autopsy
                </button>

                <button
                  onClick={() => onInspectCounterfactual(selectedCandidate)}
                  className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded text-xs font-semibold hover:bg-gray-50 transition"
                >
                  What-If
                </button>

                <button
                  onClick={() => onAddToCasebook(selectedCandidate)}
                  className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded text-xs font-semibold hover:bg-gray-50 transition flex items-center gap-1"
                >
                  <BookmarkPlus className="w-3.5 h-3.5" /> Casebook
                </button>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-400 text-xs">
              Select any candidate from the table to inspect Opportunity Destroyer falsification checks.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
