import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { RealityCheckResult } from "../types/api";
import { MetricCard } from "../components/common/MetricCard";
import { Badge } from "../components/common/Badge";
import { ShieldCheck, Play, RefreshCw, Layers, BarChart2 } from "lucide-react";

export const RealityCheckView: React.FC = () => {
  const [data, setData] = useState<RealityCheckResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    executeRealityCheck();
  }, []);

  const executeRealityCheck = async () => {
    try {
      setLoading(true);
      setError(null);
      const health = await api.getHealth();
      const dsId = health.active_dataset_id || "ds-synthetic-mcx-gold-baseline";
      const res = await api.runRealityCheck({
        dataset_id: dsId,
        pair_symbol_a: "GOLDM",
        pair_symbol_b: "GOLD",
        rolling_windows: [10, 15, 20, 30, 45],
        zscore_thresholds: [1.5, 2.0, 2.5, 3.0],
      });
      setData(res);
    } catch (err: any) {
      setError(err.message || "Reality Check failed");
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
            <ShieldCheck className="w-5 h-5 text-amber-600" />
            Opportunity Destroyer & Reality Check Engine
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Tests apparent relative-value opportunities against 12 institutional disproof falsification tests: normalization errors, transaction costs, slippage, liquidity thresholds, and multiple-testing bias.
          </p>
        </div>

        <button
          onClick={executeRealityCheck}
          disabled={loading}
          className="px-4 py-2 bg-gray-900 text-white rounded font-semibold text-xs hover:bg-gray-800 transition flex items-center gap-2 disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-white" />}
          Run Skeptical Validation
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded text-sm">{error}</div>
      )}

      {data && (
        <>
          {/* Key Diagnostic Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              label="Bootstrap p-value"
              value={data.bootstrap_p_value.toFixed(4)}
              subtext="Null: zero cointegration alpha"
              badge={
                <Badge variant={data.bootstrap_p_value < 0.05 ? "investigate" : "suppressed"}>
                  {data.bootstrap_p_value < 0.05 ? "p < 0.05" : "NOT SIGNIFICANT"}
                </Badge>
              }
            />

            <MetricCard
              label="Selection Bias Risk"
              value={data.selection_bias_risk_rating}
              subtext={`${data.total_experiments_evaluated} parameter hypotheses tested`}
              badge={<Badge variant="gold">MULTIPLE COMPARISONS</Badge>}
            />

            <MetricCard
              label="Walk-Forward Stability"
              value={`${(data.walk_forward_stability_score * 100).toFixed(0)}%`}
              subtext="Cross-window persistence"
            />

            <MetricCard
              label="Overall Verdict Survival"
              value={data.verdict_survival_rating.replace(/_/g, " ")}
              subtext="Penalty-adjusted research status"
              badge={
                <Badge variant={data.verdict_survival_rating.includes("ROBUST") ? "investigate" : "insufficient"}>
                  {data.verdict_survival_rating.includes("ROBUST") ? "SURVIVES" : "PENALIZED"}
                </Badge>
              }
            />
          </div>

          {/* Grid Sensitivity Table & Subwindow Persistence */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Parameter Grid Matrix */}
            <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3">
              <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2 border-b border-gray-100 pb-2.5">
                <Layers className="w-4 h-4 text-blue-600" /> Parameter Grid Sensitivity Matrix
              </h2>
              <div className="overflow-x-auto max-h-80">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-gray-50 text-gray-500 text-[10px] uppercase border-b border-gray-200">
                    <tr>
                      <th className="py-2 px-3">Window</th>
                      <th className="py-2 px-3">Z Threshold</th>
                      <th className="py-2 px-3">Detected</th>
                      <th className="py-2 px-3">Anomaly Rate</th>
                      <th className="py-2 px-3">Stability</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.parameter_grid_sensitivity.map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50/70">
                        <td className="py-1.5 px-3">{row.window_days}d</td>
                        <td className="py-1.5 px-3">{row.zscore_threshold.toFixed(1)}</td>
                        <td className="py-1.5 px-3 font-bold">{row.anomalies_detected}</td>
                        <td className="py-1.5 px-3">{row.anomaly_rate_pct}%</td>
                        <td className="py-1.5 px-3 font-sans">
                          <span
                            className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              row.stability === "STABLE"
                                ? "bg-emerald-100 text-emerald-800"
                                : row.stability === "SPARSE"
                                ? "bg-gray-100 text-gray-600"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {row.stability}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right: Subwindow Results */}
            <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3 flex flex-col justify-between">
              <div>
                <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2 border-b border-gray-100 pb-2.5 mb-3">
                  <BarChart2 className="w-4 h-4 text-emerald-600" /> Historical Sub-Period Consistency
                </h2>
                <div className="space-y-3">
                  {data.subwindow_results.map((sub, idx) => (
                    <div key={idx} className="border border-gray-200 rounded p-3 bg-gray-50/50 text-xs">
                      <div className="font-bold text-gray-900 mb-2">{sub.subwindow_name}</div>
                      <div className="grid grid-cols-3 gap-2 font-mono text-center">
                        <div className="bg-white border border-gray-200 rounded p-2">
                          <div className="text-[10px] text-gray-400 font-sans">Mean Spread</div>
                          <div className="font-bold text-gray-800">{sub.spread_mean_bps} bps</div>
                        </div>
                        <div className="bg-white border border-gray-200 rounded p-2">
                          <div className="text-[10px] text-gray-400 font-sans">Volatility</div>
                          <div className="font-bold text-gray-800">{sub.spread_std_bps} bps</div>
                        </div>
                        <div className="bg-white border border-gray-200 rounded p-2">
                          <div className="text-[10px] text-gray-400 font-sans">Max Shock</div>
                          <div className="font-bold text-rose-700">{sub.max_divergence_bps} bps</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-[11px] text-gray-500 bg-gray-50 border border-gray-200 rounded p-3 leading-relaxed">
                <strong>Selection Bias Disclosure:</strong> Multiple testing penalty applied (
                {data.multiple_testing_penalty_applied}). When scanning multiple lookback windows and z-score
                thresholds, apparent significance decays if false discovery rates are uncorrected.
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
