import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import {
  FileText, Download, Clock, Settings as SettingsIcon, Copy
} from "lucide-react";

export const ReportsAuditView: React.FC = () => {
  const [auditEvents, setAuditEvents] = useState<any[]>([]);
  const [settings, setSettings] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadAuditAndSettings();
  }, []);

  const loadAuditAndSettings = async () => {
    try {
      const [events, setts] = await Promise.all([api.getAudit(50), api.getSettings()]);
      setAuditEvents(events);
      setSettings(setts);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGenerating(true);
      const res = await api.generateReport();
      setReport(res);
      await loadAuditAndSettings();
    } catch (err: any) {
      alert("Failed to generate report: " + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = () => {
    if (!report?.markdown_content) return;
    navigator.clipboard.writeText(report.markdown_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadReport = () => {
    if (!report?.markdown_content) return;
    const blob = new Blob([report.markdown_content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${report.report_id}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <FileText className="w-5 h-5 text-amber-600" />
            Research Reports, Audit Trail & System Configuration
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Export reproducible research memorandums, inspect the immutable audit ledger, and verify system operating thresholds.
          </p>
        </div>

        <button
          onClick={handleGenerateReport}
          disabled={generating}
          className="px-4 py-2 bg-gray-900 text-white rounded font-semibold text-xs hover:bg-gray-800 transition flex items-center gap-2 disabled:opacity-50"
        >
          <FileText className="w-3.5 h-3.5 text-amber-400" />
          {generating ? "Compiling Dossier..." : "Compile Research Report"}
        </button>
      </div>

      {/* Generated Report Viewer */}
      {report && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-gray-900 uppercase">Compiled Report Dossier:</span>
              <span className="font-mono text-xs text-gray-600 font-semibold">{report.report_id}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={copyToClipboard}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-semibold flex items-center gap-1 transition"
              >
                <Copy className="w-3.5 h-3.5" /> {copied ? "Copied!" : "Copy Markdown"}
              </button>
              <button
                onClick={downloadReport}
                className="px-3 py-1 bg-gray-900 hover:bg-gray-800 text-white rounded text-xs font-semibold flex items-center gap-1 transition"
              >
                <Download className="w-3.5 h-3.5" /> Download (.md)
              </button>
            </div>
          </div>

          <pre className="bg-gray-50 border border-gray-200 rounded p-4 text-xs font-mono text-gray-800 overflow-x-auto max-h-96 whitespace-pre-wrap leading-relaxed">
            {report.markdown_content}
          </pre>
        </div>
      )}

      {/* Audit Trail & Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Audit Trail (8 Cols) */}
        <div className="lg:col-span-8 bg-white border border-gray-200 rounded-lg p-5 space-y-3">
          <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2 border-b border-gray-100 pb-2.5">
            <Clock className="w-4 h-4 text-gray-500" /> Immutable Audit Ledger (Last 50 Actions)
          </h2>

          <div className="overflow-x-auto max-h-[460px]">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-gray-50 text-gray-500 text-[10px] uppercase border-b border-gray-200 sticky top-0">
                <tr>
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Action Type</th>
                  <th className="py-2 px-4 font-sans">Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-[11px]">
                {auditEvents.map((e) => (
                  <tr key={e.id} className="hover:bg-gray-50/70">
                    <td className="py-2 px-3 text-gray-500 whitespace-nowrap">
                      {new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td className="py-2 px-3 font-semibold text-gray-800">{e.event_type}</td>
                    <td className="py-2 px-4 font-sans text-gray-700">{e.summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Settings & Thresholds (4 Cols) */}
        <div className="lg:col-span-4 bg-white border border-gray-200 rounded-lg p-5 space-y-3">
          <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2 border-b border-gray-100 pb-2.5">
            <SettingsIcon className="w-4 h-4 text-amber-600" /> Active Operating Parameters
          </h2>

          {settings ? (
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1.5 border-b border-gray-100">
                <span className="font-sans text-gray-500">Z-Score Significance Hurdle</span>
                <span className="font-bold text-gray-900">{settings.default_zscore_threshold} sigma</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-gray-100">
                <span className="font-sans text-gray-500">Rolling Lookback Window</span>
                <span className="font-bold text-gray-900">{settings.default_rolling_window_days} days</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-gray-100">
                <span className="font-sans text-gray-500">Min Historical Observations</span>
                <span className="font-bold text-gray-900">{settings.default_min_observations} points</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-gray-100">
                <span className="font-sans text-gray-500">Expiry Buffer Threshold</span>
                <span className="font-bold text-gray-900">{settings.default_expiry_proximity_days} days</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-gray-100">
                <span className="font-sans text-gray-500">Slippage Friction (Half)</span>
                <span className="font-bold text-gray-900">{settings.default_slippage_bps} bps</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-gray-100">
                <span className="font-sans text-gray-500">Brokerage Schedule</span>
                <span className="font-bold text-gray-900">{settings.default_brokerage_bps} bps</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="font-sans text-gray-500">MCX Exchange Fees</span>
                <span className="font-bold text-gray-900">{settings.default_exchange_fees_bps} bps</span>
              </div>
            </div>
          ) : (
            <div className="text-gray-400 text-xs py-4 text-center">Loading settings...</div>
          )}
        </div>
      </div>
    </div>
  );
};
