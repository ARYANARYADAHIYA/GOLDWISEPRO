import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { Badge } from "../components/common/Badge";
import {
  Sliders, Database, Cpu, ShieldCheck, CheckCircle2,
  RefreshCw, Save, AlertTriangle, ExternalLink
} from "lucide-react";

export const SettingsView: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [autoRetrain, setAutoRetrain] = useState(true);

  // Form states
  const [zscoreThreshold, setZscoreThreshold] = useState(2.0);
  const [rollingWindow, setRollingWindow] = useState(20);
  const [minObservations, setMinObservations] = useState(15);
  const [slippageBps, setSlippageBps] = useState(1.5);
  const [brokerageBps, setBrokerageBps] = useState(1.0);
  const [exchangeFeeBps, setExchangeFeeBps] = useState(2.1);
  const [bhavcopyUrl, setBhavcopyUrl] = useState("https://www.mcxindia.com/market-data/bhavcopy");

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const res = await api.getSettings();
      if (res.default_zscore_threshold !== undefined) setZscoreThreshold(res.default_zscore_threshold);
      if (res.default_rolling_window_days !== undefined) setRollingWindow(res.default_rolling_window_days);
      if (res.default_min_observations !== undefined) setMinObservations(res.default_min_observations);
      if (res.default_slippage_bps !== undefined) setSlippageBps(res.default_slippage_bps);
      if (res.default_brokerage_bps !== undefined) setBrokerageBps(res.default_brokerage_bps);
      if (res.default_exchange_fees_bps !== undefined) setExchangeFeeBps(res.default_exchange_fees_bps);
      if (res.auto_retraining_enabled !== undefined) setAutoRetrain(res.auto_retraining_enabled);
    } catch (e) {
      console.error("Failed to load settings", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await api.updateSetting("auto_retraining_enabled", JSON.stringify({ enabled: autoRetrain }));
      await api.updateSetting("research_thresholds", JSON.stringify({
        zscore_threshold: zscoreThreshold,
        rolling_window_days: rollingWindow,
        min_observations: minObservations,
        slippage_bps: slippageBps,
        brokerage_bps: brokerageBps,
        exchange_fees_bps: exchangeFeeBps,
        bhavcopy_url: bhavcopyUrl
      }));
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      console.error("Save error", e);
      alert("Failed to save settings: " + String(e));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500 font-mono text-sm animate-pulse">
        Loading GOLDWISE PRO System Configuration...
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Title & Save Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-gray-200 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-gray-900">Application Settings & Preferences</h1>
            <Badge variant="gold">System Configuration</Badge>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            Institutional research defaults, official MCX exchange data paths, and autonomous ML retraining policies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {saveSuccess && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Settings Saved
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-gray-900 hover:bg-black text-amber-400 rounded-md text-xs font-semibold shadow-xs transition"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save System Settings
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* ML & Autonomous Retraining Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
            <Cpu className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-bold text-gray-900">GoldWise ML & Retraining Policies</h2>
          </div>

          <div className="flex items-start justify-between gap-4 p-3 bg-gray-50 rounded-md border border-gray-200">
            <div>
              <div className="text-xs font-bold text-gray-900">Autonomous Model Retraining</div>
              <p className="text-[11px] text-gray-500 mt-0.5 leading-relaxed">
                When new MCX Bhavcopy or CSV data is imported, automatically validate observation sufficiency, run chronological holdout validation, and update Model Lab.
              </p>
            </div>
            <input
              type="checkbox"
              checked={autoRetrain}
              onChange={(e) => setAutoRetrain(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500 cursor-pointer"
            />
          </div>

          <div className="space-y-3 pt-2">
            <div>
              <label className="text-xs font-semibold text-gray-700 block mb-1">
                Minimum Observations Required for Holdout Validation
              </label>
              <input
                type="number"
                value={minObservations}
                onChange={(e) => setMinObservations(parseInt(e.target.value) || 15)}
                className="w-full text-xs font-mono px-3 py-2 border border-gray-200 rounded focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
              <span className="text-[10px] text-gray-400 mt-0.5 block">
                Prevents overfitting or premature training on sparse data regimes.
              </span>
            </div>

            <div className="p-2.5 bg-amber-50/60 border border-amber-200/60 rounded text-[11px] text-amber-900 flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <span>
                <strong>Lookahead Protection:</strong> All retraining executions enforce strict chronological splits (Train 70% / Val 15% / Test 15%) with zero random shuffling.
              </span>
            </div>
          </div>
        </div>

        {/* Official MCX Data Source Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
            <Database className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-bold text-gray-900">Official MCX Exchange Endpoints</h2>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-gray-700 block mb-1">
                MCX Daily Bhavcopy Archive Endpoint
              </label>
              <input
                type="text"
                value={bhavcopyUrl}
                onChange={(e) => setBhavcopyUrl(e.target.value)}
                className="w-full text-xs font-mono px-3 py-2 border border-gray-200 rounded focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
            </div>

            <div className="p-3 bg-gray-50 border border-gray-200 rounded space-y-1.5 text-[11px]">
              <div className="font-semibold text-gray-800">Verified Bullion Derivative Contracts:</div>
              <ul className="list-disc list-inside text-gray-600 font-mono space-y-0.5 text-[10px]">
                <li>GOLD (1 kg trading unit, quoted per 10g, 995 purity)</li>
                <li>GOLDM (100g trading unit, quoted per 10g, 995 purity)</li>
                <li>GOLDTEN (100g trading unit, quoted per 100g, 995 purity)</li>
                <li>GOLDGUINEA (8g trading unit, quoted per 8g, 999 purity)</li>
                <li>GOLDPETAL (1g trading unit, quoted per 1g, 999 purity)</li>
              </ul>
            </div>

            <div className="pt-1 flex items-center gap-2">
              <a
                href="https://www.mcxindia.com/market-data/bhavcopy"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-amber-800 hover:text-amber-900 font-medium"
              >
                <span>Visit MCX Bhavcopy Portal</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>

        {/* Quantitative Screening Thresholds */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
            <Sliders className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-bold text-gray-900">Relative-Value Screening Thresholds</h2>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-gray-700 block mb-1">
                Robust Z-Score Threshold (MAD)
              </label>
              <input
                type="number"
                step="0.1"
                value={zscoreThreshold}
                onChange={(e) => setZscoreThreshold(parseFloat(e.target.value) || 2.0)}
                className="w-full text-xs font-mono px-3 py-2 border border-gray-200 rounded focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
              <span className="text-[10px] text-gray-400 mt-0.5 block">Standard: 2.0 (95.4% confidence)</span>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-700 block mb-1">
                Rolling Lookback Window (Days)
              </label>
              <input
                type="number"
                value={rollingWindow}
                onChange={(e) => setRollingWindow(parseInt(e.target.value) || 20)}
                className="w-full text-xs font-mono px-3 py-2 border border-gray-200 rounded focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
              <span className="text-[10px] text-gray-400 mt-0.5 block">Trading sessions (10-60)</span>
            </div>
          </div>
        </div>

        {/* Transaction Friction & Cost Engine Defaults */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-bold text-gray-900">Cost Survival Friction Schedule</h2>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-700 block mb-1">
                Slippage (bps)
              </label>
              <input
                type="number"
                step="0.1"
                value={slippageBps}
                onChange={(e) => setSlippageBps(parseFloat(e.target.value) || 1.5)}
                className="w-full text-xs font-mono px-3 py-2 border border-gray-200 rounded focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
              <span className="text-[10px] text-gray-400 mt-0.5 block">Default: 1.5 bps</span>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-700 block mb-1">
                Brokerage (bps)
              </label>
              <input
                type="number"
                step="0.1"
                value={brokerageBps}
                onChange={(e) => setBrokerageBps(parseFloat(e.target.value) || 1.0)}
                className="w-full text-xs font-mono px-3 py-2 border border-gray-200 rounded focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
              <span className="text-[10px] text-gray-400 mt-0.5 block">Institutional: 1.0 bps</span>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-700 block mb-1">
                Exchange Fees (bps)
              </label>
              <input
                type="number"
                step="0.1"
                value={exchangeFeeBps}
                onChange={(e) => setExchangeFeeBps(parseFloat(e.target.value) || 2.1)}
                className="w-full text-xs font-mono px-3 py-2 border border-gray-200 rounded focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
              <span className="text-[10px] text-gray-400 mt-0.5 block">MCX + CTT: ~2.1 bps</span>
            </div>
          </div>

          <div className="p-2.5 bg-gray-50 border border-gray-200 rounded text-[11px] text-gray-600">
            Total baseline cost hurdle: <span className="font-mono font-bold text-gray-900">{(slippageBps * 2 + brokerageBps * 2 + exchangeFeeBps).toFixed(1)} bps</span> round-turn. Any prospective spread narrower than this is immediately suppressed.
          </div>
        </div>
      </div>
    </div>
  );
};
