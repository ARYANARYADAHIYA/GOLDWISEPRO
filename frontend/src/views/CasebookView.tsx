import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { PaperResearchRecord } from "../types/api";
import { Bookmark, Plus, Edit3 } from "lucide-react";

export const CasebookView: React.FC = () => {
  const [records, setRecords] = useState<PaperResearchRecord[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [showModal, setShowModal] = useState(false);

  // New Case Form State
  const [pair, setPair] = useState("GOLDM/GOLD");
  const [obsDate, setObsDate] = useState("2026-05-15");
  const [verdict, setVerdict] = useState("INVESTIGATE");
  const [spreadBps, setSpreadBps] = useState(48.5);
  const [rationale, setRationale] = useState("");

  useEffect(() => {
    loadCasebook();
  }, []);

  const loadCasebook = async () => {
    try {
      const res = await api.getCasebook();
      setRecords(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCasebook({
        symbol_pair: pair,
        observation_date: obsDate,
        initial_verdict: verdict,
        spread_bps: spreadBps,
        rationale: rationale || "High robust z-score divergence with all 12 Opportunity Destroyer tests cleared.",
        entry_price_spread: spreadBps,
      });
      setShowModal(false);
      loadCasebook();
    } catch (err: any) {
      alert("Failed to create casebook record: " + err.message);
    }
  };

  const handleUpdateStatus = async (id: string, newStatus: string) => {
    const note = prompt("Enter review note / observed outcome:");
    if (note === null) return;
    try {
      await fetch(`/api/casebook/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ status: newStatus, notes: note }),
      });
      loadCasebook();
    } catch (err: any) {
      alert("Update failed: " + err.message);
    }
  };

  const filtered = records.filter((r) => {
    if (statusFilter === "ALL") return true;
    return r.status === statusFilter;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-amber-600" />
            Research Workbench & Opportunity Casebook
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Institutional research workbench tracking analytical experiments, prospective hypotheses, configurations, and post-friction outcomes.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="px-3.5 py-1.5 bg-gray-900 text-white rounded text-xs font-semibold hover:bg-gray-800 transition flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" /> Log New Research Case
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 pb-2 text-xs">
        <span className="text-gray-500 font-medium">Status Filter:</span>
        {(["ALL", "PROSPECTIVE", "VALIDATED", "DISPROVED", "EXPIRED"] as const).map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition ${
              statusFilter === st
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {st} ({st === "ALL" ? records.length : records.filter((r) => r.status === st).length})
          </button>
        ))}
      </div>

      {/* Casebook Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 text-gray-600 font-medium uppercase text-[10px] tracking-wider border-b border-gray-200">
              <tr>
                <th className="py-2.5 px-4">Case ID</th>
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Pair</th>
                <th className="py-2.5 px-3">Entry Spread</th>
                <th className="py-2.5 px-4">Research Rationale</th>
                <th className="py-2.5 px-3">Horizon</th>
                <th className="py-2.5 px-3">Disposition</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono text-[11px]">
              {filtered.map((caseItem) => (
                <tr key={caseItem.id} className="hover:bg-gray-50/80 transition-colors">
                  <td className="py-2.5 px-4 text-gray-900 font-semibold">{caseItem.id}</td>
                  <td className="py-2.5 px-3 text-gray-600">{caseItem.observation_date}</td>
                  <td className="py-2.5 px-3 font-sans font-bold text-gray-800">{caseItem.symbol_pair}</td>
                  <td className="py-2.5 px-3 text-amber-900 font-bold tabular-nums">
                    {caseItem.spread_bps.toFixed(1)} bps
                  </td>
                  <td className="py-2.5 px-4 font-sans text-xs text-gray-600 max-w-xs truncate">
                    {caseItem.rationale}
                    {caseItem.notes && <div className="text-[10px] text-gray-400 italic mt-0.5">Note: {caseItem.notes}</div>}
                  </td>
                  <td className="py-2.5 px-3 font-sans text-gray-500">{caseItem.expected_horizon_days}d</td>
                  <td className="py-2.5 px-3 font-sans">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        caseItem.status === "VALIDATED"
                          ? "bg-emerald-100 text-emerald-800"
                          : caseItem.status === "DISPROVED"
                          ? "bg-rose-100 text-rose-800"
                          : caseItem.status === "EXPIRED"
                          ? "bg-gray-100 text-gray-700"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {caseItem.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right font-sans">
                    <button
                      onClick={() => handleUpdateStatus(caseItem.id, caseItem.status === "PROSPECTIVE" ? "VALIDATED" : "DISPROVED")}
                      className="text-xs font-semibold text-gray-700 hover:text-gray-900 underline flex items-center gap-1 ml-auto"
                    >
                      <Edit3 className="w-3 h-3" /> Update Disposition
                    </button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-gray-400 font-sans text-xs">
                    No research cases matching current status filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal for creating a case */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg border border-gray-200 shadow-xl max-w-lg w-full p-6 space-y-4">
            <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
              <Bookmark className="w-4 h-4 text-amber-600" /> Log Prospective Research Decision
            </h2>
            <form onSubmit={handleCreateCase} className="space-y-3 text-xs">
              <div>
                <label className="block text-gray-600 font-medium mb-1">Contract Pair</label>
                <input
                  type="text"
                  value={pair}
                  onChange={(e) => setPair(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-1.5 font-semibold"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-600 font-medium mb-1">Observation Date</label>
                  <input
                    type="date"
                    value={obsDate}
                    onChange={(e) => setObsDate(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-1.5"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-600 font-medium mb-1">Entry Spread (bps)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={spreadBps}
                    onChange={(e) => setSpreadBps(parseFloat(e.target.value) || 0)}
                    className="w-full border border-gray-300 rounded px-3 py-1.5"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-gray-600 font-medium mb-1">Initial Hypothesis / Verdict</label>
                <select
                  value={verdict}
                  onChange={(e) => setVerdict(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-1.5 font-semibold"
                >
                  <option value="INVESTIGATE">INVESTIGATE</option>
                  <option value="VALIDATED">VALIDATED</option>
                  <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
                  <option value="WATCH">WATCH</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-600 font-medium mb-1">Research Rationale</label>
                <textarea
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  rows={3}
                  className="w-full border border-gray-300 rounded px-3 py-1.5 text-xs"
                  placeholder="Detail why this relative-value deviation is being tracked..."
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 text-gray-600 rounded hover:bg-gray-100 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-gray-900 text-white rounded font-semibold hover:bg-gray-800"
                >
                  Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
