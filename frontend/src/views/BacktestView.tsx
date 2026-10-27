import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { BacktestResult } from "../types/api";
import { MetricCard } from "../components/common/MetricCard";
import { ChartCanvas, type DataPoint } from "../components/common/ChartCanvas";
import { TrendingUp, Play, RefreshCw } from "lucide-react";

export const BacktestView: React.FC = () => {
  const [symbolA, setSymbolA] = useState("GOLDM");
  const [symbolB, setSymbolB] = useState("GOLD");
  const [entryZscore, setEntryZscore] = useState(2.0);
  const [exitZscore, setExitZscore] = useState(0.5);
  const [holdingDays, setHoldingDays] = useState(5);
  const [positionSize] = useState(1000000);
  const [slippageBps, setSlippageBps] = useState(3.0);

  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    executeBacktest();
  }, []);

  const executeBacktest = async () => {
    try {
      setLoading(true);
      setError(null);
      const health = await api.getHealth();
      const dsId = health.active_dataset_id || "ds-synthetic-mcx-gold-baseline";
      const res = await api.runBacktest({
        dataset_id: dsId,
        pair_symbol_a: symbolA,
        pair_symbol_b: symbolB,
        entry_zscore: entryZscore,
        exit_zscore: exitZscore,
        holding_period_days: holdingDays,
        position_size_inr: positionSize,
        slippage_bps: slippageBps,
        execution_delay_days: 1, // T+1 chronological enforcement
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Backtest execution failed");
    } finally {
      setLoading(false);
    }
  };

  const equityData: DataPoint[] =
    result?.equity_curve?.map((pt) => ({
      x: pt.date,
      y: pt.equity_inr,
    })) || [];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header & Controls Deck */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-4 mb-4">
          <div>
            <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              Walk-Forward Backtesting Lab
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Strict chronological time-series evaluation with T+1 execution delay and deducted roundtrip transaction costs.
            </p>
          </div>

          <button
            onClick={executeBacktest}
            disabled={loading}
            className="px-4 py-2 bg-gray-900 text-white rounded font-semibold text-xs hover:bg-gray-800 transition flex items-center gap-2 disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-white" />}
            Run Walk-Forward Backtest
          </button>
        </div>

        {/* Configuration inputs */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-xs">
          <div>
            <label className="block text-gray-500 font-medium mb-1">Contract Leg A</label>
            <select
              value={symbolA}
              onChange={(e) => setSymbolA(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-semibold text-gray-800"
            >
              <option value="GOLDM">GOLDM (100g)</option>
              <option value="GOLD">GOLD (1kg)</option>
              <option value="GOLDGUINEA">GOLDGUINEA (8g)</option>
              <option value="GOLDPETAL">GOLDPETAL (1g)</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Benchmark Leg B</label>
            <select
              value={symbolB}
              onChange={(e) => setSymbolB(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-semibold text-gray-800"
            >
              <option value="GOLD">GOLD (1kg Benchmark)</option>
              <option value="GOLDM">GOLDM (100g)</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Entry Z-Score</label>
            <input
              type="number"
              step="0.1"
              value={entryZscore}
              onChange={(e) => setEntryZscore(parseFloat(e.target.value) || 2.0)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-800"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Exit Z-Score</label>
            <input
              type="number"
              step="0.1"
              value={exitZscore}
              onChange={(e) => setExitZscore(parseFloat(e.target.value) || 0.5)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-800"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Max Holding (Days)</label>
            <input
              type="number"
              value={holdingDays}
              onChange={(e) => setHoldingDays(parseInt(e.target.value) || 5)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-800"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Slippage (bps)</label>
            <input
              type="number"
              step="0.5"
              value={slippageBps}
              onChange={(e) => setSlippageBps(parseFloat(e.target.value) || 3.0)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-800"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded text-sm">{error}</div>
      )}

      {result && (
        <>
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard
              label="Net Return (Post-Cost)"
              value={`${result.net_return_pct > 0 ? "+" : ""}${result.net_return_pct}%`}
              subtext={`Gross: ${result.gross_return_pct}%`}
              className={result.net_return_pct >= 0 ? "border-emerald-200" : "border-rose-200"}
            />

            <MetricCard
              label="Cost Drag (INR)"
              value={`Rs ${result.cost_drag_inr.toLocaleString()}`}
              subtext={`${result.total_costs_bps} bps friction`}
            />

            <MetricCard
              label="Sharpe Ratio (Ann.)"
              value={result.sharpe_ratio.toFixed(2)}
              subtext="Risk-free rate: 6.5%"
            />

            <MetricCard
              label="Max Drawdown"
              value={`-${result.max_drawdown_pct}%`}
              subtext="Peak to trough"
            />

            <MetricCard
              label="Win Rate"
              value={`${result.win_rate}%`}
              subtext={`Profit Factor: ${result.profit_factor}`}
            />

            <MetricCard
              label="Executed Trades"
              value={result.executed_trades}
              subtext={`${result.total_signals} total signals`}
            />
          </div>

          {/* Interactive Equity Curve */}
          <ChartCanvas
            data={equityData}
            title={`Walk-Forward Simulated Portfolio Equity (INR)`}
            seriesName="Portfolio Value"
            color="#059669"
            height={260}
          />

          {/* Trade Log Table */}
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider">
                Chronological Trade Ledger ({result.trades.length} Executed Trades)
              </h2>
              <span className="text-xs text-gray-400 font-mono">T+1 Execution Delay Enforced</span>
            </div>

            <div className="overflow-x-auto max-h-80">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-50 text-gray-600 font-medium uppercase text-[10px] tracking-wider sticky top-0 border-b border-gray-200">
                  <tr>
                    <th className="py-2.5 px-3">#</th>
                    <th className="py-2.5 px-3">Signal Date</th>
                    <th className="py-2.5 px-3">Entry Date</th>
                    <th className="py-2.5 px-3">Exit Date</th>
                    <th className="py-2.5 px-3">Entry Spread</th>
                    <th className="py-2.5 px-3">Exit Spread</th>
                    <th className="py-2.5 px-3">Friction</th>
                    <th className="py-2.5 px-3">Net PnL (INR)</th>
                    <th className="py-2.5 px-3">Return</th>
                    <th className="py-2.5 px-4">Exit Trigger</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-mono text-[11px]">
                  {result.trades.map((t) => (
                    <tr key={t.trade_id} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-2 px-3 text-gray-400 font-sans">{t.trade_id}</td>
                      <td className="py-2 px-3 text-gray-500">{t.signal_date}</td>
                      <td className="py-2 px-3 text-gray-900 font-medium">{t.entry_date}</td>
                      <td className="py-2 px-3 text-gray-900">{t.exit_date}</td>
                      <td className="py-2 px-3 text-gray-700">{t.entry_spread_bps} bps</td>
                      <td className="py-2 px-3 text-gray-700">{t.exit_spread_bps} bps</td>
                      <td className="py-2 px-3 text-gray-500">Rs {t.total_cost_inr.toFixed(0)}</td>
                      <td
                        className={`py-2 px-3 font-bold ${
                          t.net_pnl_inr >= 0 ? "text-emerald-700" : "text-rose-700"
                        }`}
                      >
                        {t.net_pnl_inr > 0 ? "+" : ""}Rs {t.net_pnl_inr.toFixed(0)}
                      </td>
                      <td
                        className={`py-2 px-3 font-bold ${
                          t.net_return_pct >= 0 ? "text-emerald-700" : "text-rose-700"
                        }`}
                      >
                        {t.net_return_pct > 0 ? "+" : ""}{t.net_return_pct}%
                      </td>
                      <td className="py-2 px-4 font-sans text-[10px] text-gray-600">
                        {t.exit_reason}
                      </td>
                    </tr>
                  ))}
                  {result.trades.length === 0 && (
                    <tr>
                      <td colSpan={10} className="py-8 text-center text-gray-400 font-sans text-xs">
                        No trades executed under current z-score hurdle and holding parameters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="text-[11px] text-gray-500 bg-gray-50 border border-gray-200 rounded p-3 leading-relaxed">
            <strong>Execution Realism Disclosure:</strong> {result.execution_realism_disclaimer}
          </div>
        </>
      )}
    </div>
  );
};
