import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { ExecutiveOverview } from "../types/api";
import { MetricCard } from "../components/common/MetricCard";
import { Badge } from "../components/common/Badge";
import {
  Activity, Database, ShieldAlert, Award, FileText, CheckCircle2,
  TrendingUp, Clock, AlertTriangle
} from "lucide-react";

interface OverviewViewProps {
  onNavigate: (viewId: string) => void;
  onSelectCandidate?: (candidateId: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate }) => {
  const [data, setData] = useState<ExecutiveOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getOverview();
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load overview data");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-500 font-mono text-sm">
          <span className="w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
          Loading Executive Overview telemetry...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700 m-6">
        <div className="font-bold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" /> Error loading overview
        </div>
        <div className="text-sm mt-1">{error}</div>
        <button
          onClick={loadOverview}
          className="mt-3 px-3 py-1.5 bg-red-600 text-white rounded text-xs font-semibold hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const ds = data.active_dataset;
  const dq = data.data_quality;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner: Provenance & Freshness */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <h1 className="text-lg font-bold text-gray-900 tracking-tight">
              Executive Research Overview
            </h1>
            <Badge variant={ds.is_synthetic ? "synthetic" : "real"}>
              {ds.is_synthetic ? "Synthetic Demonstration Mode" : "Verified MCX Bhavcopy"}
            </Badge>
          </div>
          <p className="text-xs text-gray-500 font-sans max-w-2xl">
            {ds.is_synthetic
              ? "Operating in deterministic synthetic demonstration mode with 8 calibrated market & error injection scenarios. Real-market conclusions are withheld."
              : `Active dataset '${ds.name}' imported with verified MCX contract settlement records.`}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate("scanner")}
            className="px-3.5 py-1.5 bg-gray-900 text-white text-xs font-semibold rounded hover:bg-gray-800 transition flex items-center gap-1.5"
          >
            <Activity className="w-3.5 h-3.5 text-amber-400" /> Run Relative Value Scan
          </button>
          <button
            onClick={() => onNavigate("reports")}
            className="px-3.5 py-1.5 bg-white border border-gray-300 text-gray-700 text-xs font-semibold rounded hover:bg-gray-50 transition flex items-center gap-1.5"
          >
            <FileText className="w-3.5 h-3.5 text-gray-500" /> Export Dossier
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Active Candidates"
          value={data.active_candidates_summary.investigate}
          subtext={`${data.active_candidates_summary.suppressed} suppressed by Destroyer`}
          icon={<Activity className="w-4 h-4 text-emerald-600" />}
          badge={<Badge variant="investigate">INVESTIGATE</Badge>}
        />

        <MetricCard
          label="Data Quality Score"
          value={`${dq.score}/100`}
          subtext={dq.status.replace(/_/g, " ")}
          icon={<ShieldAlert className="w-4 h-4 text-amber-600" />}
          badge={
            <span
              className={`text-xs font-bold ${
                dq.score >= 80 ? "text-emerald-700" : "text-amber-700"
              }`}
            >
              {dq.score >= 80 ? "AUDIT PASS" : "WARNING"}
            </span>
          }
        />

        <MetricCard
          label="Dataset Observations"
          value={ds.row_count}
          subtext={`${ds.start_date} → ${ds.end_date}`}
          icon={<Database className="w-4 h-4 text-blue-600" />}
          badge={<span className="text-xs font-mono text-gray-500">{ds.instruments.length} Pairs</span>}
        />

        <MetricCard
          label="Hypothetical Backtest"
          value={`${data.latest_backtest.net_return_pct > 0 ? "+" : ""}${data.latest_backtest.net_return_pct}%`}
          subtext={`Sharpe: ${data.latest_backtest.sharpe_ratio} | Win: ${data.latest_backtest.win_rate}%`}
          icon={<TrendingUp className="w-4 h-4 text-emerald-600" />}
          badge={<span className="text-xs text-gray-400">T+1 execution</span>}
        />
      </div>

      {/* Two-Column Telemetry: Research Engine & Recent Audit Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Research Status & Falsification Breakdown */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
              <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-amber-600" />
                Latest Scan & Falsification Verdicts
              </h2>
              <span className="text-xs text-gray-400 font-mono">
                {data.latest_scan.pair || "GOLDM/GOLD"}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-emerald-50/60 border border-emerald-200/60 rounded p-3 text-center">
                <div className="text-xs text-emerald-800 font-semibold mb-0.5">INVESTIGATE</div>
                <div className="text-2xl font-bold text-emerald-900 font-mono">
                  {data.latest_scan.investigate_count}
                </div>
                <div className="text-[11px] text-emerald-700 mt-1">Cleared 12 Destroyer checks</div>
              </div>

              <div className="bg-rose-50/60 border border-rose-200/60 rounded p-3 text-center">
                <div className="text-xs text-rose-800 font-semibold mb-0.5">SUPPRESSED</div>
                <div className="text-2xl font-bold text-rose-900 font-mono">
                  {data.latest_scan.suppressed_count}
                </div>
                <div className="text-[11px] text-rose-700 mt-1">Falsified by cost, expiry or data</div>
              </div>

              <div className="bg-amber-50/60 border border-amber-200/60 rounded p-3 text-center">
                <div className="text-xs text-amber-800 font-semibold mb-0.5">INSUFFICIENT DATA</div>
                <div className="text-2xl font-bold text-amber-900 font-mono">
                  {data.latest_scan.insufficient_count}
                </div>
                <div className="text-[11px] text-amber-700 mt-1">&lt; 15 historical points</div>
              </div>
            </div>

            <div className="text-xs text-gray-600 leading-relaxed bg-gray-50 border border-gray-200 rounded p-3">
              <strong className="text-gray-900">Research Integrity Notice:</strong> Candidates labeled{" "}
              <span className="font-semibold text-emerald-800">INVESTIGATE</span> represent genuine
              statistical divergences that survived quotation unit checks, 995 vs 999 fineness adjustments,
              transaction cost thresholds, and expiry delivery window protections. They do NOT guarantee
              arbitrage profit.
            </div>
          </div>

          {/* Machine Learning Model State */}
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-3">
              <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-600" />
                Active Model Telemetry
              </h2>
              <button
                onClick={() => onNavigate("models")}
                className="text-xs font-semibold text-amber-700 hover:text-amber-800"
              >
                Model Lab &rarr;
              </button>
            </div>

            <div className="flex items-center justify-between text-xs py-2 border-b border-gray-100">
              <span className="text-gray-500">Active Model Name</span>
              <span className="font-mono font-semibold text-gray-900">
                {data.latest_model.name || "Isolation Forest (Default Benchmark)"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs py-2 border-b border-gray-100">
              <span className="text-gray-500">Model Architecture</span>
              <span className="font-mono text-gray-700">
                {data.latest_model.model_type || "Unsupervised Isolation Forest"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs py-2">
              <span className="text-gray-500">Evaluation Protocol</span>
              <span className="text-gray-700 font-mono">Chronological Train (70%) / Val (15%) / Test (15%)</span>
            </div>
          </div>
        </div>

        {/* Right Col: Recent Audit Trail */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-3">
              <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-500" />
                Recent Research Audit Log
              </h2>
              <button
                onClick={() => onNavigate("reports")}
                className="text-xs text-amber-700 hover:underline font-semibold"
              >
                Full Trail
              </button>
            </div>

            <div className="divide-y divide-gray-100">
              {data.recent_research_activity.slice(0, 6).map((act) => (
                <div key={act.id} className="py-2.5 text-xs">
                  <div className="flex items-center justify-between font-mono text-[10px] text-gray-400 mb-0.5">
                    <span>{act.event_type}</span>
                    <span>{new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <div className="text-gray-800 font-medium leading-snug">{act.summary}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-gray-100 mt-4 text-[11px] text-gray-400">
            Append-only audit ledger actively recording model training, scans, CSV imports, and casebook entries.
          </div>
        </div>
      </div>
    </div>
  );
};
