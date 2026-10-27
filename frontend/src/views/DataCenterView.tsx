import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { DatasetSummary, DataIntegrityReport } from "../types/api";
import { Badge } from "../components/common/Badge";
import {
  Database, UploadCloud, ShieldAlert, Hash, Check, RefreshCw,
  AlertCircle, FileSpreadsheet, CheckCircle2
} from "lucide-react";

export const DataCenterView: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [integrity, setIntegrity] = useState<DataIntegrityReport | null>(null);
  const [activeDatasetId, setActiveDatasetId] = useState<string>("");
  const [collectionStatus, setCollectionStatus] = useState<any>(null);

  // Automated collection state
  const [collecting, setCollecting] = useState(false);
  const [collectResult, setCollectResult] = useState<any>(null);
  const [seedingReal, setSeedingReal] = useState(false);
  const [seedSuccessMsg, setSeedSuccessMsg] = useState<string | null>(null);

  // Manual Upload Form
  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState("");
  const [description, setDescription] = useState("");
  const [dateFormat, setDateFormat] = useState("DD/MM/YYYY");
  const [uploading, setUploading] = useState(false);
  const [uploadReport, setUploadReport] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [dsList, health, integ, colStat] = await Promise.all([
        api.getDatasets(),
        api.getHealth(),
        api.getIntegrity(),
        api.getDataCollectionStatus()
      ]);
      setDatasets(dsList);
      setActiveDatasetId(health.active_dataset_id || "");
      setIntegrity(integ);
      setCollectionStatus(colStat);
    } catch (err) {
      console.error(err);
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await api.activateDataset(id);
      setActiveDatasetId(id);
      await loadData();
    } catch (err: any) {
      alert("Failed to activate dataset: " + err.message);
    }
  };

  const handleCollectMcx = async () => {
    try {
      setCollecting(true);
      setCollectResult(null);
      const res = await api.collectMcx();
      setCollectResult(res);
      await loadData();
    } catch (err: any) {
      setCollectResult({
        status: "ERROR",
        message: err.message || "MCX collection check encountered a network error."
      });
    } finally {
      setCollecting(false);
    }
  };

  const handleSeedRealMcx = async () => {
    try {
      setSeedingReal(true);
      setSeedSuccessMsg(null);
      const res = await api.seedRealMcx();
      if (res.success) {
        setSeedSuccessMsg(`Successfully imported & activated authentic MCX Gold History dataset with ${res.validation_report?.row_count} observations!`);
        await loadData();
      }
    } catch (err: any) {
      alert("Failed to seed real MCX data: " + err.message);
    } finally {
      setSeedingReal(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    try {
      setUploading(true);
      setUploadError(null);
      setUploadReport(null);
      const res = await api.uploadCsv(
        file,
        datasetName || file.name,
        description,
        dateFormat
      );
      setUploadReport(res.validation_report);
      if (res.success) {
        setFile(null);
        setDatasetName("");
        setDescription("");
        await loadData();
      }
    } catch (err: any) {
      setUploadError(err.message || "Dataset upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <Database className="w-5 h-5 text-amber-600" />
            MCX Data Center & Ingestion Pipeline
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Real Multi Commodity Exchange of India (MCX) historical data pipeline for GOLD, GOLDM, GOLDTEN, GOLDGUINEA and GOLDPETAL.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleCollectMcx}
            disabled={collecting}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded text-xs font-semibold border border-gray-300 transition"
          >
            {collecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Check Daily MCX Bhavcopy
          </button>

          <button
            onClick={handleSeedRealMcx}
            disabled={seedingReal}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-gray-900 hover:bg-black text-amber-400 rounded text-xs font-semibold shadow-xs transition"
          >
            {seedingReal ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <FileSpreadsheet className="w-3.5 h-3.5" />}
            Load Real MCX Gold History
          </button>
        </div>
      </div>

      {collectionStatus && collectionStatus.last_collection_event?.summary && (
        <div className="bg-white border border-gray-200 rounded-md px-4 py-2 text-xs text-gray-600 flex flex-wrap items-center justify-between gap-2 font-mono">
          <span>Provenance Ledger: <strong className="text-gray-900 font-sans">{collectionStatus.last_collection_event.summary}</strong></span>
          <span className="text-[10px] text-gray-400">{collectionStatus.last_collection_event.timestamp?.slice(0, 19)}</span>
        </div>
      )}

      {seedSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="font-medium">{seedSuccessMsg}</span>
        </div>
      )}

      {/* MCX Collection Status Alert / Result */}
      {collectResult && (
        <div className={`p-4 rounded-lg border text-xs space-y-2 ${
          collectResult.status === "DOWNLOADED"
            ? "bg-emerald-50 border-emerald-200 text-emerald-900"
            : collectResult.status === "MARKET_CLOSED"
            ? "bg-blue-50 border-blue-200 text-blue-900"
            : "bg-amber-50 border-amber-300 text-amber-900"
        }`}>
          <div className="flex items-center justify-between font-bold">
            <span className="flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4" />
              MCX Automated Collection Result: {collectResult.status}
            </span>
            <span className="font-mono text-[11px]">{collectResult.target_date}</span>
          </div>
          <p className="text-xs leading-relaxed">{collectResult.message}</p>
          <div className="text-[11px] font-mono text-gray-600 flex flex-wrap gap-3 pt-1 border-t border-amber-200/50">
            <span>Source: {collectResult.provenance_url}</span>
            {collectResult.fallback_ready && (
              <span className="text-amber-800 font-semibold font-sans">
                &bull; Ingestion fallback ready: Use manual upload below for official Bhavcopy CSV/Excel exports.
              </span>
            )}
          </div>
        </div>
      )}

      {/* Data Integrity Guardian Audit */}
      {integrity && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-emerald-600" />
                <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                  Data Quality & Integrity Guardian
                </h2>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                Evaluates {integrity.total_observations_audited} active observations in database with zero lookahead.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-2xl font-bold font-mono text-gray-900">
                  {integrity.overall_quality_score}/100
                </div>
                <div className="text-[10px] text-gray-400 font-sans uppercase">Quality Score</div>
              </div>
              <Badge variant={integrity.overall_quality_score >= 80 ? "investigate" : "suppressed"}>
                {integrity.status.replace(/_/g, " ")}
              </Badge>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div className="bg-gray-50 border border-gray-100 rounded p-3 text-center">
              <div className="text-[10px] text-gray-400 font-sans">OHLC Violations</div>
              <div className="text-base font-bold text-gray-900 mt-1">
                {integrity.metrics.invalid_ohlc_count}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-100 rounded p-3 text-center">
              <div className="text-[10px] text-gray-400 font-sans">Price Outliers</div>
              <div className="text-base font-bold text-gray-900 mt-1">
                {integrity.metrics.price_outlier_count}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-100 rounded p-3 text-center">
              <div className="text-[10px] text-gray-400 font-sans">Stale Observations</div>
              <div className="text-base font-bold text-gray-900 mt-1">
                {integrity.metrics.stale_price_count}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-100 rounded p-3 text-center">
              <div className="text-[10px] text-gray-400 font-sans">Unexpected Date Gaps</div>
              <div className="text-base font-bold text-gray-900 mt-1">
                {integrity.metrics.unexpected_gaps_count}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dataset Registry & CSV/Excel Import Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Dataset Registry (7 Cols) */}
        <div className="lg:col-span-7 bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-2.5">
            <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
              Stored Datasets in Database ({datasets.length})
            </h2>
            <span className="text-[11px] text-gray-400 font-mono">Real-time sync</span>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {datasets.map((ds) => {
              const isActive = ds.id === activeDatasetId;
              const isReal = ds.source_type !== "SYNTHETIC";
              return (
                <div
                  key={ds.id}
                  className={`border rounded-lg p-3.5 transition-colors ${
                    isActive ? "border-amber-400 bg-amber-50/20 shadow-xs" : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-900 text-xs">{ds.name}</span>
                        <Badge variant={isReal ? "real" : "synthetic"}>
                          {isReal ? "LIVE MCX DATA" : "SYNTHETIC DEMO"}
                        </Badge>
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">{ds.description}</div>
                    </div>

                    {!isActive ? (
                      <button
                        onClick={() => handleActivate(ds.id)}
                        className="px-2.5 py-1 text-xs font-semibold bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 shrink-0"
                      >
                        Activate
                      </button>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded shrink-0">
                        <Check className="w-3.5 h-3.5" /> ACTIVE IN TERMINAL
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-gray-500 font-mono mt-2 pt-2 border-t border-gray-100">
                    <span>Rows: <strong className="text-gray-900">{ds.row_count}</strong></span>
                    <span>Dates: {ds.start_date} &rarr; {ds.end_date}</span>
                    <span className="truncate max-w-[150px]">Instruments: {ds.instruments}</span>
                    <span className="flex items-center gap-1 ml-auto text-[10px]">
                      <Hash className="w-3 h-3 text-gray-400" /> {ds.file_hash?.slice(0, 10)}...
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Manual Ingestion Fallback (5 Cols) */}
        <div className="lg:col-span-5 bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-gray-100 pb-2.5">
            <UploadCloud className="w-4 h-4 text-amber-600" /> Manual Bhavcopy Ingestion Fallback
          </h2>

          <p className="text-[11px] text-gray-500">
            Upload official MCX Bhavcopy or Historical Data in <strong>CSV or Excel (.xlsx, .xls)</strong> format. Automatically maps columns, eliminates duplicates, and recalculates INR/g quotation bases.
          </p>

          <form onSubmit={handleUpload} className="space-y-3 text-xs">
            <div>
              <label className="block text-gray-600 font-medium mb-1">Dataset Name</label>
              <input
                type="text"
                placeholder="e.g., MCX Gold Daily Bhavcopy 2026"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                required
              />
            </div>

            <div>
              <label className="block text-gray-600 font-medium mb-1">Description (Optional)</label>
              <input
                type="text"
                placeholder="Notes on trade dates, session extract, provenance..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-gray-600 font-medium mb-1">Date Format Ambiguity Rule</label>
              <select
                value={dateFormat}
                onChange={(e) => setDateFormat(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-semibold text-gray-800"
              >
                <option value="DD/MM/YYYY">DD/MM/YYYY (Indian Standard)</option>
                <option value="MM/DD/YYYY">MM/DD/YYYY (US Format)</option>
              </select>
            </div>

            <div>
              <label className="block text-gray-600 font-medium mb-1">Bhavcopy File (CSV or Excel)</label>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-gray-100 file:font-semibold"
                required
              />
            </div>

            <button
              type="submit"
              disabled={uploading || !file}
              className="w-full py-2 bg-gray-900 text-white font-semibold rounded text-xs hover:bg-gray-800 transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Ingesting & Retraining...
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" /> Ingest Dataset & Retrain
                </>
              )}
            </button>
          </form>

          {uploadError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded text-xs">
              {uploadError}
            </div>
          )}

          {uploadReport && (
            <div
              className={`p-3 rounded text-xs border ${
                uploadReport.is_valid
                  ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                  : "bg-red-50 border-red-200 text-red-900"
              }`}
            >
              <div className="font-bold mb-1">
                {uploadReport.is_valid ? "Ingestion Succeeded" : "Ingestion Rejected"}
              </div>
              <div className="space-y-0.5 font-mono text-[11px]">
                <div>Imported Observations: {uploadReport.row_count}</div>
                <div>Duplicate Records Dropped: {uploadReport.duplicate_count}</div>
                <div>Instruments Mapped: {uploadReport.instruments}</div>
                <div>Hash: {uploadReport.file_hash?.slice(0, 16)}...</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
