import React from "react";
import type { AnomalyCandidate } from "../types/api";
import { Badge } from "../components/common/Badge";
import {
  FileSearch, CheckCircle2, AlertTriangle, ArrowLeft,
  Scale, Compass, DollarSign, Info
} from "lucide-react";

interface AutopsyViewProps {
  candidate: AnomalyCandidate | null;
  onBack: () => void;
  onNavigateToCasebook?: (candidate: AnomalyCandidate) => void;
}

export const AutopsyView: React.FC<AutopsyViewProps> = ({
  candidate,
  onBack,
  onNavigateToCasebook,
}) => {
  if (!candidate) {
    return (
      <div className="p-8 text-center text-gray-500 max-w-xl mx-auto space-y-3">
        <FileSearch className="w-8 h-8 text-gray-400 mx-auto" />
        <h2 className="text-sm font-bold text-gray-800">No Candidate Selected for Autopsy</h2>
        <p className="text-xs text-gray-500">
          Run the Relative Value Scanner and click "Signal Autopsy" on any candidate to inspect its evidence dossier.
        </p>
        <button
          onClick={onBack}
          className="mt-3 px-3 py-1.5 bg-gray-900 text-white rounded text-xs font-semibold"
        >
          &larr; Back to Scanner
        </button>
      </div>
    );
  }

  const autopsy = candidate.autopsy_features;
  const economic = autopsy?.economic_survival_summary;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <button
            onClick={onBack}
            className="text-xs font-semibold text-gray-500 hover:text-gray-900 flex items-center gap-1 mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Scanner
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-gray-900 tracking-tight">
              Signal Evidence & Autopsy Dossier
            </h1>
            <Badge
              variant={
                candidate.verdict === "INVESTIGATE"
                  ? "investigate"
                  : candidate.verdict === "SUPPRESSED"
                  ? "suppressed"
                  : "insufficient"
              }
            >
              {candidate.verdict}
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500 font-mono mt-1">
            <span>Candidate ID: {candidate.id}</span>
            <span>Pair: {candidate.symbol_a} / {candidate.symbol_b}</span>
            <span>Date: {candidate.timestamp}</span>
          </div>
        </div>

        {onNavigateToCasebook && (
          <button
            onClick={() => onNavigateToCasebook(candidate)}
            className="px-3.5 py-1.5 bg-gray-900 text-white text-xs font-semibold rounded hover:bg-gray-800 transition"
          >
            Track in Research Casebook
          </button>
        )}
      </div>

      {/* Probability vs Anomaly Score Disclosure Alert */}
      <div className="bg-amber-50/70 border border-amber-200 rounded-lg p-4 text-xs text-amber-900 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong className="font-semibold text-amber-950">Quantitative Epistemology Notice:</strong> Anomaly
          scores measure standardized deviation from empirical training manifolds (MAD-adjusted z-score:{" "}
          <span className="font-mono font-bold">{candidate.robust_zscore?.toFixed(2)}</span>). They do{" "}
          <strong>NOT</strong> represent probability of profit. No model output constitutes a guarantee of
          execution at daily settlement prices.
        </div>
      </div>

      {/* Grid: Feature Attributions & Alternative Explanations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Feature Perturbation Attribution */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <div className="border-b border-gray-100 pb-3 flex items-center justify-between">
            <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
              <Scale className="w-4 h-4 text-amber-600" /> Feature Perturbation Attribution
            </h2>
            <span className="text-[11px] text-gray-400 font-mono">Model-Agnostic</span>
          </div>

          <p className="text-xs text-gray-500 leading-relaxed">
            Measures the relative contribution of each observation feature to the composite anomaly score by
            perturbing the value to its historical median.
          </p>

          <div className="space-y-3 pt-2">
            {autopsy?.feature_attributions?.map((feat, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-medium text-gray-700">
                  <span>{feat.feature_name}</span>
                  <span className="font-mono font-bold text-gray-900">
                    {feat.relative_importance_pct.toFixed(1)}%
                  </span>
                </div>
                {/* Progress Bar */}
                <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-600 h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(100, feat.relative_importance_pct)}%` }}
                  />
                </div>
                <div className="text-[11px] text-gray-500">{feat.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Alternative Explanations & Counter-Evidence */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4 flex flex-col justify-between">
          <div>
            <div className="border-b border-gray-100 pb-3 flex items-center justify-between mb-3">
              <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
                <Compass className="w-4 h-4 text-blue-600" /> Alternative Explanations Examined
              </h2>
              <span className="text-[11px] text-gray-400 font-mono">Hypothesis Testing</span>
            </div>

            <div className="space-y-2.5">
              {autopsy?.alternative_explanations_examined?.map((hypo, idx) => (
                <div
                  key={idx}
                  className="bg-gray-50 border border-gray-200 rounded p-2.5 text-xs flex items-start gap-2"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="flex items-center justify-between font-semibold text-gray-800">
                      <span>{hypo.hypothesis}</span>
                      <span className="text-[10px] font-mono text-emerald-700">{hypo.status}</span>
                    </div>
                    <div className="text-[11px] text-gray-600 mt-0.5">{hypo.evidence}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Counter-Evidence section */}
            {autopsy?.counter_evidence && autopsy.counter_evidence.length > 0 && (
              <div className="mt-4 pt-3 border-t border-gray-100">
                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Counter-Evidence & Weakening Conditions
                </div>
                <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
                  {autopsy.counter_evidence.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Economic Survival Card */}
          {economic && (
            <div className="bg-gray-50 border border-gray-200 rounded p-3 text-xs">
              <div className="font-bold text-gray-800 uppercase text-[10px] tracking-wider mb-2 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-emerald-600" /> Economic Friction Survival Check
              </div>
              <div className="grid grid-cols-3 gap-2 font-mono text-center">
                <div className="bg-white border border-gray-200 rounded p-2">
                  <div className="text-[10px] text-gray-400 font-sans">Gross Spread</div>
                  <div className="font-bold text-gray-900">{economic.gross_spread_bps} bps</div>
                </div>
                <div className="bg-white border border-gray-200 rounded p-2">
                  <div className="text-[10px] text-gray-400 font-sans">Friction Barrier</div>
                  <div className="font-bold text-gray-600">{economic.estimated_friction_bps} bps</div>
                </div>
                <div className="bg-white border border-gray-200 rounded p-2">
                  <div className="text-[10px] text-gray-400 font-sans">Hypothetical Net</div>
                  <div
                    className={`font-bold ${
                      economic.hypothetical_net_bps > 0 ? "text-emerald-700" : "text-rose-700"
                    }`}
                  >
                    {economic.hypothetical_net_bps} bps
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
