import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { AnomalyCandidate } from "../types/api";
import { GitCompare, Play, RefreshCw } from "lucide-react";

interface CounterfactualViewProps {
  initialCandidate?: AnomalyCandidate | null;
}

export const CounterfactualView: React.FC<CounterfactualViewProps> = ({ initialCandidate }) => {
  const [candidateId, setCandidateId] = useState(initialCandidate?.id || "");
  const [candidates, setCandidates] = useState<AnomalyCandidate[]>([]);
  const [modSlippage, setModSlippage] = useState(6.0);
  const [modZscore, setModZscore] = useState(2.5);
  const [modExpiryBuffer, setModExpiryBuffer] = useState(5);

  const [simulation, setSimulation] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRecentCandidates();
  }, []);

  const loadRecentCandidates = async () => {
    try {
      const health = await api.getHealth();
      const dsId = health.active_dataset_id || "ds-synthetic-mcx-gold-baseline";
      const scanRes = await api.runScan({ dataset_id: dsId });
      setCandidates(scanRes.candidates);
      if (!candidateId && scanRes.candidates.length > 0) {
        setCandidateId(scanRes.candidates[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const runSimulation = async () => {
    if (!candidateId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.runCounterfactual({
        candidate_id: candidateId,
        modified_slippage_bps: modSlippage,
        modified_zscore_threshold: modZscore,
        modified_expiry_buffer_days: modExpiryBuffer,
      });
      setSimulation(res);
    } catch (err: any) {
      setError(err.message || "Counterfactual simulation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-amber-600" />
            Stress Testing & Counterfactual Simulation
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Evaluate sensitivity to volatility surges, friction costs, wider bid-ask spreads, missing observations, and expiry proximity.
          </p>
        </div>

        <button
          onClick={runSimulation}
          disabled={loading || !candidateId}
          className="px-4 py-2 bg-gray-900 text-white rounded font-semibold text-xs hover:bg-gray-800 transition flex items-center gap-2 disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-white" />}
          Run What-If Simulation
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded text-sm">{error}</div>
      )}

      {/* Control Panel: Candidate Picker & Perturbed Inputs */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-4">
          Select Candidate & Perturb Operating Assumptions
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="block text-gray-500 font-medium mb-1">Target Anomaly Candidate</label>
            <select
              value={candidateId}
              onChange={(e) => setCandidateId(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-900"
            >
              {candidates.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} | {c.timestamp} | {c.verdict} ({(c.percentage_spread * 100).toFixed(1)} bps)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Perturbed Slippage (bps)</label>
            <input
              type="number"
              step="0.5"
              value={modSlippage}
              onChange={(e) => setModSlippage(parseFloat(e.target.value) || 0)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono"
            />
            <span className="text-[10px] text-gray-400">Baseline was 3.0 bps</span>
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Perturbed Z-Score Hurdle</label>
            <input
              type="number"
              step="0.1"
              value={modZscore}
              onChange={(e) => setModZscore(parseFloat(e.target.value) || 0)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono"
            />
            <span className="text-[10px] text-gray-400">Baseline was 2.0 sigma</span>
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Expiry Safe Buffer (Days)</label>
            <input
              type="number"
              value={modExpiryBuffer}
              onChange={(e) => setModExpiryBuffer(parseInt(e.target.value) || 0)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono"
            />
            <span className="text-[10px] text-gray-400">Baseline was 3 days</span>
          </div>
        </div>
      </div>

      {/* Comparative Results Display */}
      {simulation && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
              Simulation Verdict Comparison
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 font-medium">Verdict Changed:</span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded ${
                  simulation.verdict_changed ? "bg-rose-100 text-rose-800" : "bg-emerald-100 text-emerald-800"
                }`}
              >
                {simulation.verdict_changed ? "YES (FRAGILE)" : "NO (ROBUST)"}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Original */}
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50/50 space-y-2">
              <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Original Research Verdict</div>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-gray-900 font-mono">
                  {simulation.original_verdict}
                </span>
                <span className="text-xs font-mono text-gray-500">Score: {simulation.original_score}</span>
              </div>
              <div className="text-xs text-gray-500">Evaluated under baseline 3.0 bps slippage and 2.0 sigma hurdle.</div>
            </div>

            {/* Counterfactual */}
            <div
              className={`border rounded-lg p-4 space-y-2 ${
                simulation.counterfactual_verdict === "INVESTIGATE"
                  ? "border-emerald-300 bg-emerald-50/30"
                  : "border-rose-300 bg-rose-50/30"
              }`}
            >
              <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Counterfactual What-If Result</div>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold font-mono text-gray-900">
                  {simulation.counterfactual_verdict}
                </span>
                <span className="text-xs font-mono text-gray-500">Score: {simulation.counterfactual_score}</span>
              </div>
              <div className="text-xs text-gray-600 font-medium">{simulation.robustness_assessment}</div>
            </div>
          </div>

          {/* Causal Drivers */}
          <div className="bg-gray-50 border border-gray-200 rounded p-3 text-xs space-y-1">
            <div className="font-bold text-gray-800 uppercase text-[10px] tracking-wider mb-1">
              Active Perturbation Drivers:
            </div>
            {simulation.driver_factors.map((f: string, i: number) => (
              <div key={i} className="text-gray-700 font-mono">
                &bull; {f}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
