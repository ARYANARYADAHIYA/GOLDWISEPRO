import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { MLModelRecord, TournamentResult } from "../types/api";
import { Badge } from "../components/common/Badge";
import { MetricCard } from "../components/common/MetricCard";
import { ChartCanvas } from "../components/common/ChartCanvas";
import {
  Award, Play, RefreshCw, Cpu, Layers, AlertCircle
} from "lucide-react";

export const ModelLabView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"lab" | "tournament" | "drift" | "forecast">("lab");
  const [models, setModels] = useState<MLModelRecord[]>([]);
  const [tournament, setTournament] = useState<TournamentResult | null>(null);
  const [drift, setDrift] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);

  const [modelType, setModelType] = useState("ISOLATION_FOREST");
  const [modelName, setModelName] = useState("Isolation Forest (5% Contamination)");
  const [contamination, setContamination] = useState(0.05);
  const [nEstimators, setNEstimators] = useState(100);

  const [training, setTraining] = useState(false);
  const [retrainingAll, setRetrainingAll] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
    loadTournament();
    loadDrift();
    loadForecast();
  }, []);

  const loadModels = async () => {
    try {
      const res = await api.getModels();
      setModels(res);
    } catch (err) {
      console.error(err);
    }
  };

  const loadTournament = async () => {
    try {
      const res = await api.getTournament();
      setTournament(res);
    } catch (err) {
      console.error(err);
    }
  };

  const loadDrift = async () => {
    try {
      const res = await api.getDrift();
      setDrift(res);
    } catch (err) {
      console.error(err);
    }
  };

  const loadForecast = async () => {
    try {
      const res = await api.getForecast();
      setForecast(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRetrainAll = async () => {
    try {
      setRetrainingAll(true);
      setStatusMsg("Executing automated retraining pipeline for Isolation Forest & Price Forecaster on active dataset...");
      const res = await api.retrainModels();
      setStatusMsg(`Retraining complete! Status: ${res.status}. Price Forecaster Hit Rate: ${res.price_forecasting?.metrics?.candidate?.directional_accuracy_pct || 'N/A'}%`);
      await Promise.all([loadModels(), loadTournament(), loadForecast()]);
    } catch (err: any) {
      setStatusMsg("Retraining error: " + err.message);
    } finally {
      setRetrainingAll(false);
    }
  };

  const handleTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setTraining(true);
      setStatusMsg("Executing chronological train/val/test pipeline & fitting scikit-learn model...");
      const health = await api.getHealth();
      const dsId = health.active_dataset_id || "ds-synthetic-mcx-gold-baseline";
      const trained = await api.trainModel({
        name: modelName,
        model_type: modelType,
        dataset_id: dsId,
        contamination: contamination,
        n_estimators: nEstimators,
      });
      setStatusMsg(`Model trained successfully! Saved to artifact '${trained.artifact_path}'`);
      await loadModels();
      await loadTournament();
    } catch (err: any) {
      setStatusMsg("Training error: " + err.message);
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-600" />
            GOLDWISE PRO Model Lab & Research Suite
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Institutional machine learning anomaly detection, baseline tournaments, drift surveillance, and price forecasting.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRetrainAll}
            disabled={retrainingAll}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-900 hover:bg-black text-amber-400 rounded-md text-xs font-semibold shadow-xs transition"
          >
            {retrainingAll ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Retrain Model Suite
          </button>

          {/* Tab Switcher */}
          <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg text-xs font-semibold">
            <button
              onClick={() => setActiveTab("lab")}
              className={`px-3 py-1.5 rounded transition ${
                activeTab === "lab" ? "bg-white text-gray-900 shadow-xs" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Model Lab & Registry
            </button>
            <button
              onClick={() => setActiveTab("forecast")}
              className={`px-3 py-1.5 rounded transition ${
                activeTab === "forecast" ? "bg-white text-gray-900 shadow-xs" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Price Forecaster
            </button>
            <button
              onClick={() => setActiveTab("tournament")}
              className={`px-3 py-1.5 rounded transition ${
                activeTab === "tournament" ? "bg-white text-gray-900 shadow-xs" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Model Tournament
            </button>
            <button
              onClick={() => setActiveTab("drift")}
              className={`px-3 py-1.5 rounded transition ${
                activeTab === "drift" ? "bg-white text-gray-900 shadow-xs" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Drift & Calibration
            </button>
          </div>
        </div>
      </div>

      {statusMsg && (
        <div className="p-3 bg-blue-50 border border-blue-200 text-blue-900 rounded text-xs flex items-center justify-between">
          <span>{statusMsg}</span>
          <button onClick={() => setStatusMsg(null)} className="text-blue-500 font-bold ml-2">
            &times;
          </button>
        </div>
      )}

      {/* TAB 1: MODEL LAB & REGISTRY */}
      {activeTab === "lab" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Training Control (5 Cols) */}
          <div className="lg:col-span-5 bg-white border border-gray-200 rounded-lg p-5 space-y-4">
            <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2 border-b border-gray-100 pb-2.5">
              <Cpu className="w-4 h-4 text-amber-600" /> Train Candidate Anomaly Model
            </h2>

            <form onSubmit={handleTrain} className="space-y-3 text-xs">
              <div>
                <label className="block text-gray-600 font-medium mb-1">Architecture</label>
                <select
                  value={modelType}
                  onChange={(e) => {
                    setModelType(e.target.value);
                    if (e.target.value === "BASELINE_STATISTICAL") {
                      setModelName("Robust Statistical Baseline (MAD)");
                    } else {
                      setModelName("Isolation Forest (5% Contamination)");
                    }
                  }}
                  className="w-full bg-gray-50 border border-gray-200 rounded px-3 py-1.5 font-semibold text-gray-800"
                >
                  <option value="ISOLATION_FOREST">Model B: Scikit-Learn IsolationForest</option>
                  <option value="BASELINE_STATISTICAL">Model A: Robust Statistical Baseline (MAD)</option>
                  <option value="SUPERVISED_RIDGE">Model C: Supervised Outcome (Conditional)</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-600 font-medium mb-1">Model Version Tag</label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded px-3 py-1.5"
                  required
                />
              </div>

              {modelType === "ISOLATION_FOREST" && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-gray-600 font-medium mb-1">Contamination Rate</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      max="0.20"
                      value={contamination}
                      onChange={(e) => setContamination(parseFloat(e.target.value) || 0.05)}
                      className="w-full bg-gray-50 border border-gray-200 rounded px-3 py-1.5 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-gray-600 font-medium mb-1">N Estimators</label>
                    <input
                      type="number"
                      value={nEstimators}
                      onChange={(e) => setNEstimators(parseInt(e.target.value) || 100)}
                      className="w-full bg-gray-50 border border-gray-200 rounded px-3 py-1.5 font-mono"
                    />
                  </div>
                </div>
              )}

              <div className="bg-gray-50 border border-gray-200 rounded p-3 text-[11px] text-gray-600 space-y-1">
                <div className="font-semibold text-gray-800">Chronological Partitioning Protocol:</div>
                <div>&bull; Training Slice: 70% (Earliest dates, strictly no lookahead)</div>
                <div>&bull; Validation Slice: 15% (Hyperparameter tuning)</div>
                <div>&bull; Protected Test Slice: 15% (Zero contamination holdout)</div>
              </div>

              <button
                type="submit"
                disabled={training}
                className="w-full py-2 bg-gray-900 text-white font-semibold rounded text-xs hover:bg-gray-800 transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {training ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Training Model...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" /> Train & Persist Model
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Model Registry List (7 Cols) */}
          <div className="lg:col-span-7 bg-white border border-gray-200 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 pb-2.5">
              <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-amber-600" /> Model Registry ({models.length})
              </h2>
              <span className="text-[11px] text-gray-400 font-mono">SQLite + Disk (.joblib)</span>
            </div>

            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {models.length === 0 ? (
                <div className="p-6 text-center text-gray-400 text-xs">
                  No trained ML models registered yet. Use the training controls on the left or click "Retrain Model Suite".
                </div>
              ) : (
                models.map((m) => (
                  <div key={m.id} className="border border-gray-200 rounded-lg p-3.5 hover:border-gray-300 transition">
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900 text-xs">{m.name}</span>
                          <span className="text-[10px] text-gray-400 font-mono">({m.version})</span>
                          {m.is_active && (
                            <Badge variant="real">Active Deployed</Badge>
                          )}
                        </div>
                        <div className="text-[11px] text-gray-500 font-mono mt-0.5">
                          Type: {m.model_type} &bull; Dataset: {m.dataset_id}
                        </div>
                      </div>
                      <Badge variant={m.status === "TRAINED" ? "investigate" : "suppressed"}>
                        {m.status}
                      </Badge>
                    </div>

                    <div className="text-[11px] text-gray-500 font-mono bg-gray-50 p-2 rounded mt-2 truncate">
                      Artifact: {m.artifact_path || "In-Memory"}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PRICE FORECASTER */}
      {activeTab === "forecast" && (
        <div className="space-y-6">
          {forecast && forecast.status === "INSUFFICIENT_DATA" ? (
            <div className="bg-amber-50 border border-amber-300 rounded-lg p-6 text-center space-y-2">
              <AlertCircle className="w-6 h-6 text-amber-700 mx-auto" />
              <h3 className="text-sm font-bold text-amber-900">Insufficient Observations for Chronological Holdout</h3>
              <p className="text-xs text-amber-800 max-w-lg mx-auto">
                {forecast.message || "Price forecasting requires at least 25 consecutive aligned observations to prevent lookahead and ensure statistically valid holdout evaluation."}
              </p>
              <div className="pt-2">
                <button
                  onClick={handleRetrainAll}
                  className="px-3 py-1.5 bg-gray-900 text-amber-400 text-xs font-semibold rounded shadow-xs"
                >
                  Ingest MCX Real Data & Retrain
                </button>
              </div>
            </div>
          ) : forecast && forecast.metrics ? (
            <>
              {/* Top Forecaster KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  label="Directional Accuracy (Hit Rate)"
                  value={`${forecast.metrics.candidate?.directional_accuracy_pct || 0}%`}
                  subtext="Sign prediction on chronological holdout"
                  trend="up"
                  badge={<Badge variant="investigate">Empirical Holdout</Badge>}
                />

                <MetricCard
                  label="Candidate Price MAE"
                  value={`₹${forecast.metrics.candidate?.mae_price_inr_per_g || 0}/g`}
                  subtext={`RMSE: ₹${forecast.metrics.candidate?.rmse_price_inr_per_g || 0}/g`}
                />

                <MetricCard
                  label="Naive Baseline MAE"
                  value={`₹${forecast.metrics.baseline?.mae_price_inr_per_g || 0}/g`}
                  subtext={`Persistence benchmark: y(t+1) = y(t)`}
                />

                <MetricCard
                  label="Edge vs Naive Benchmark"
                  value={`${forecast.metrics.edge?.mae_improvement_pct >= 0 ? "+" : ""}${forecast.metrics.edge?.mae_improvement_pct || 0}%`}
                  subtext="MAE error reduction vs baseline"
                  trend={forecast.metrics.edge?.mae_improvement_pct > 0 ? "up" : "down"}
                  badge={
                    <Badge variant={forecast.metrics.edge?.mae_improvement_pct > 0 ? "investigate" : "suppressed"}>
                      {forecast.metrics.edge?.mae_improvement_pct > 0 ? "Outperforming" : "Neutral"}
                    </Badge>
                  }
                />
              </div>

              {/* Holdout Price Trajectory Chart */}
              <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <div>
                    <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                      Chronological Holdout Price Trajectory: Candidate Forecast vs Actual Settlement
                    </h2>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Evaluated strictly out-of-sample on unseen test slice (Zero lookahead guarantee).
                    </p>
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                      Candidate Forecast
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                      Actual MCX Settle
                    </span>
                  </div>
                </div>

                <ChartCanvas
                  data={(forecast.test_series || []).map((pt: any) => ({
                    x: pt.timestamp,
                    y: pt.predicted_price,
                    y2: pt.actual_price,
                    label: `Date: ${pt.timestamp} | Pred: ₹${pt.predicted_price} | Act: ₹${pt.actual_price}`
                  }))}
                  title="Price Prediction Holdout (INR/g)"
                  height={260}
                  color="#d97706"
                  color2="#2563eb"
                  seriesName="Predicted Price"
                  series2Name="Actual Price"
                />
              </div>

              {/* Lagged Features & Attribution */}
              {forecast.feature_importance && (
                <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3">
                  <h3 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                    Lagged Feature Regression Weights (%)
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                    {Object.entries(forecast.feature_importance).map(([fname, weight]: [string, any]) => (
                      <div key={fname} className="p-3 bg-gray-50 border border-gray-200 rounded">
                        <div className="text-[10px] text-gray-500 font-sans truncate">{fname}</div>
                        <div className="text-base font-bold text-gray-900 mt-0.5">{weight}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="p-8 text-center text-gray-400 text-xs">
              Loading price forecasting evaluation...
            </div>
          )}
        </div>
      )}

      {/* TAB 3: MODEL TOURNAMENT */}
      {activeTab === "tournament" && tournament && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
              <div>
                <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                  Model Tournament & Out-of-Sample Evaluation
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  Chronological benchmark comparison across statistical and unsupervised architectures.
                </p>
              </div>
              <Badge variant="investigate">
                Benchmark Active
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {tournament.models.map((entry) => (
                <div key={entry.model_id} className="border border-gray-200 rounded-lg p-4 bg-gray-50/50">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-bold text-gray-900">{entry.model_name}</span>
                    {entry.is_benchmark_baseline && <Badge variant="gold">Benchmark</Badge>}
                  </div>
                  <div className="text-[11px] text-gray-500 mb-3">{entry.evaluation_notes}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="bg-white border border-gray-200 rounded p-2">
                      <div className="text-[10px] text-gray-400 font-sans">Detection Rate</div>
                      <div className="font-bold text-gray-900">{entry.detection_rate_pct}%</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-2">
                      <div className="text-[10px] text-gray-400 font-sans">Stability Score</div>
                      <div className="font-bold text-gray-900">{entry.stability_score}</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-2">
                      <div className="text-[10px] text-gray-400 font-sans">Median Score</div>
                      <div className="font-bold text-gray-900">{entry.median_anomaly_score}</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-2">
                      <div className="text-[10px] text-gray-400 font-sans">Inference Latency</div>
                      <div className="font-bold text-gray-900">{entry.runtime_ms} ms</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pairwise Agreement Matrix */}
            <div className="border-t border-gray-200 pt-4">
              <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2">
                Pairwise Anomaly Detection Agreement Matrix (Jaccard Index)
              </h3>
              <div className="overflow-x-auto">
                <table className="text-xs font-mono">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-500">
                      <th className="py-2 px-3 text-left">Model</th>
                      {Object.keys(tournament.pairwise_agreement_matrix).map((k) => (
                        <th key={k} className="py-2 px-3 text-center">
                          {k}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(tournament.pairwise_agreement_matrix).map(([m1, row]) => (
                      <tr key={m1} className="border-b border-gray-100">
                        <td className="py-2 px-3 font-semibold text-gray-800">{m1}</td>
                        {Object.values(row).map((val, i) => (
                          <td
                            key={i}
                            className={`py-2 px-3 text-center font-bold ${
                              val >= 0.8 ? "text-emerald-700 bg-emerald-50/40" : "text-gray-700"
                            }`}
                          >
                            {(val * 100.0).toFixed(0)}%
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: DRIFT & CALIBRATION */}
      {activeTab === "drift" && drift && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
              <div>
                <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                  Feature Distribution Drift (Population Stability Index - PSI)
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  Compares training reference distributions against trailing inference observations.
                </p>
              </div>
              <Badge
                variant={
                  drift.overall_drift_status === "HEALTHY_STABLE" ? "investigate" : "suppressed"
                }
              >
                {drift.overall_drift_status}
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              {drift.feature_drift_breakdown?.map((f: any) => (
                <div key={f.feature_name} className="border border-gray-200 rounded p-3 bg-gray-50/40 text-xs">
                  <div className="font-semibold text-gray-800 truncate mb-1">{f.feature_name}</div>
                  <div className="flex items-baseline justify-between mb-2">
                    <span className="text-xs text-gray-400 font-sans">PSI Metric:</span>
                    <span
                      className={`text-base font-bold font-mono ${
                        f.psi_score < 0.1 ? "text-emerald-700" : "text-amber-700"
                      }`}
                    >
                      {f.psi_score.toFixed(3)}
                    </span>
                  </div>
                  <div className="text-[10px] text-gray-500 font-mono space-y-0.5">
                    <div>Train Mean: {f.train_mean.toFixed(2)}</div>
                    <div>Recent Mean: {f.recent_mean.toFixed(2)}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded p-3 leading-relaxed">
              <strong>Retraining Policy:</strong> PSI &lt; 0.10 indicates stable distributions. A feature with PSI
              &gt; 0.25 flags significant market regime shift requiring researcher investigation and potential model retraining.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
