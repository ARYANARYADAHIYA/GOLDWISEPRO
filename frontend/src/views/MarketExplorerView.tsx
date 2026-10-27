import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { ChartCanvas, type DataPoint } from "../components/common/ChartCanvas";
import { Badge } from "../components/common/Badge";
import { Download, SlidersHorizontal, RefreshCw } from "lucide-react";

export const MarketExplorerView: React.FC = () => {
  const [symbolA, setSymbolA] = useState("GOLDM");
  const [symbolB, setSymbolB] = useState("GOLD");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const symbols = ["GOLD", "GOLDM", "GOLDGUINEA", "GOLDPETAL", "GOLDTEN"];

  useEffect(() => {
    loadData();
  }, [symbolA, symbolB]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getMarketExplorer(symbolA, symbolB);
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load market data");
    } finally {
      setLoading(false);
    }
  };

  const exportCsv = () => {
    if (!data?.series?.length) return;
    const headers = [
      "Timestamp",
      `${symbolA}_Price`,
      `${symbolB}_Price`,
      `${symbolA}_PureGram`,
      `${symbolB}_PureGram`,
      "PercentageSpread_pct",
      "RobustZScore",
      "Percentile",
      "Verdict",
    ];
    const rows = data.series.map((s: any) => [
      s.timestamp,
      s.price_a,
      s.price_b,
      s.normalized_a,
      s.normalized_b,
      s.percentage_spread,
      s.robust_zscore ?? "",
      s.percentile ?? "",
      s.verdict,
    ]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e: any[]) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `goldwise_${symbolA}_${symbolB}_spread.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Convert series to Chart DataPoints
  const normalizedChartData: DataPoint[] =
    data?.series?.map((s: any) => ({
      x: s.timestamp,
      y: s.normalized_a,
      y2: s.normalized_b,
    })) || [];

  const spreadChartData: DataPoint[] =
    data?.series?.map((s: any) => ({
      x: s.timestamp,
      y: s.percentage_spread * 100.0, // in bps
      y2: (s.rolling_median || 0) * 100.0,
    })) || [];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header & Controls */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight">Market Explorer & Basis Tracker</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Compare historical quoted prices, normalized pure-gold equivalents, and rolling relative value spreads.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5">
            <SlidersHorizontal className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-gray-500 font-medium">Leg A:</span>
            <select
              value={symbolA}
              onChange={(e) => setSymbolA(e.target.value)}
              className="bg-transparent font-bold text-gray-900 outline-none"
            >
              {symbols.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>

            <span className="text-gray-400 mx-1">/</span>

            <span className="text-gray-500 font-medium">Leg B:</span>
            <select
              value={symbolB}
              onChange={(e) => setSymbolB(e.target.value)}
              className="bg-transparent font-bold text-gray-900 outline-none"
            >
              {symbols.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={loadData}
            className="p-1.5 border border-gray-200 rounded hover:bg-gray-50 text-gray-600"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>

          <button
            onClick={exportCsv}
            disabled={!data?.series?.length}
            className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 text-xs font-semibold rounded hover:bg-gray-50 flex items-center gap-1.5 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" /> Export Series CSV
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded text-sm">{error}</div>
      )}

      {/* Dual Synchronized Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCanvas
          data={normalizedChartData}
          title={`Normalized Pure Gold Equivalent Price (Rs / gram)`}
          seriesName={`${symbolA} Pure/g`}
          series2Name={`${symbolB} Pure/g`}
          color="#c5a059"
          color2="#2563eb"
          height={260}
        />

        <ChartCanvas
          data={spreadChartData}
          title={`Relative Percentage Spread & Rolling Median (Basis Points)`}
          seriesName="Spread (bps)"
          series2Name="Rolling Median (bps)"
          color="#10b981"
          color2="#6b7280"
          height={260}
          showZeroLine={true}
        />
      </div>

      {/* Observation-Level Detail Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider">
            Observation-Level Detail Records ({data?.series?.length || 0} Points)
          </h2>
          <span className="text-xs text-gray-500 font-mono">
            {symbolA} vs {symbolB}
          </span>
        </div>

        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 text-gray-600 font-medium uppercase text-[10px] tracking-wider sticky top-0 border-b border-gray-200">
              <tr>
                <th className="py-2.5 px-4">Date</th>
                <th className="py-2.5 px-3">{symbolA} Quoted</th>
                <th className="py-2.5 px-3">{symbolB} Quoted</th>
                <th className="py-2.5 px-3">{symbolA} Pure/g</th>
                <th className="py-2.5 px-3">{symbolB} Pure/g</th>
                <th className="py-2.5 px-3">Spread (bps)</th>
                <th className="py-2.5 px-3">Robust Z</th>
                <th className="py-2.5 px-3">Percentile</th>
                <th className="py-2.5 px-4">Verdict</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono text-[11px]">
              {data?.series?.slice(-50).map((row: any, idx: number) => (
                <tr key={idx} className="hover:bg-gray-50/80 transition-colors">
                  <td className="py-2 px-4 text-gray-900 font-medium">{row.timestamp}</td>
                  <td className="py-2 px-3 text-gray-700 tabular-nums">{row.price_a.toFixed(2)}</td>
                  <td className="py-2 px-3 text-gray-700 tabular-nums">{row.price_b.toFixed(2)}</td>
                  <td className="py-2 px-3 text-amber-900 font-semibold tabular-nums">
                    {row.normalized_a.toFixed(2)}
                  </td>
                  <td className="py-2 px-3 text-blue-900 font-semibold tabular-nums">
                    {row.normalized_b.toFixed(2)}
                  </td>
                  <td
                    className={`py-2 px-3 font-bold tabular-nums ${
                      row.percentage_spread >= 0 ? "text-emerald-700" : "text-rose-700"
                    }`}
                  >
                    {(row.percentage_spread * 100.0).toFixed(1)}
                  </td>
                  <td className="py-2 px-3 text-gray-800 tabular-nums">
                    {row.robust_zscore !== null ? row.robust_zscore.toFixed(2) : "—"}
                  </td>
                  <td className="py-2 px-3 text-gray-600 tabular-nums">
                    {row.percentile !== null ? `${row.percentile.toFixed(1)}%` : "—"}
                  </td>
                  <td className="py-2 px-4 font-sans">
                    <Badge
                      variant={
                        row.verdict === "INVESTIGATE"
                          ? "investigate"
                          : row.verdict === "SUPPRESSED"
                          ? "suppressed"
                          : "insufficient"
                      }
                    >
                      {row.verdict}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
