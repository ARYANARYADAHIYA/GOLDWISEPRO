import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { CostSimulationResult } from "../types/api";
import { MetricCard } from "../components/common/MetricCard";
import { Badge } from "../components/common/Badge";
import { DollarSign, Sliders, RefreshCw } from "lucide-react";

export const CostSimulatorView: React.FC = () => {
  const [goldPrice, setGoldPrice] = useState(75000);
  const [lotGrams, setLotGrams] = useState(100);
  const [positionLots, setPositionLots] = useState(1);
  const [brokerageBps, setBrokerageBps] = useState(1.5);
  const [exchangeFeesBps, setExchangeFeesBps] = useState(1.0);
  const [slippageBps, setSlippageBps] = useState(1.5);

  const [result, setResult] = useState<CostSimulationResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    recalculate();
  }, [goldPrice, lotGrams, positionLots, brokerageBps, exchangeFeesBps, slippageBps]);

  const recalculate = async () => {
    try {
      setLoading(true);
      const res = await api.runCostSimulation({
        quoted_price_per_10g: goldPrice,
        contract_lot_grams: lotGrams,
        position_lots: positionLots,
        brokerage_bps: brokerageBps,
        exchange_fees_bps: exchangeFeesBps,
        slippage_bps: slippageBps,
      });
      setResult(res);
    } catch (err) {
      console.error(err);
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
            <DollarSign className="w-5 h-5 text-amber-600" />
            MCX Transaction Cost & Friction Survival Simulator
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Model official statutory charges, exchange fees, brokerage, GST, and execution market microstructure friction.
          </p>
        </div>

        <button
          onClick={recalculate}
          className="p-1.5 border border-gray-200 rounded hover:bg-gray-50 text-gray-600"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Control Sliders & Inputs */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-4 flex items-center gap-1.5">
          <Sliders className="w-4 h-4 text-gray-500" /> Execution Friction Parameters
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-xs">
          <div>
            <label className="block text-gray-500 font-medium mb-1">Gold Price (Rs/10g)</label>
            <input
              type="number"
              step="500"
              value={goldPrice}
              onChange={(e) => setGoldPrice(parseFloat(e.target.value) || 75000)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-900"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Contract Size</label>
            <select
              value={lotGrams}
              onChange={(e) => setLotGrams(parseFloat(e.target.value) || 100)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-semibold text-gray-800"
            >
              <option value="100">GOLDM (100 grams)</option>
              <option value="1000">GOLD (1000 grams)</option>
              <option value="8">GOLDGUINEA (8 grams)</option>
              <option value="1">GOLDPETAL (1 gram)</option>
              <option value="10">GOLDTEN (10 grams)</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Position Lots</label>
            <input
              type="number"
              min="1"
              value={positionLots}
              onChange={(e) => setPositionLots(parseInt(e.target.value) || 1)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-900"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Brokerage (bps)</label>
            <input
              type="number"
              step="0.5"
              value={brokerageBps}
              onChange={(e) => setBrokerageBps(parseFloat(e.target.value) || 1.5)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-900"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Exchange Fee (bps)</label>
            <input
              type="number"
              step="0.2"
              value={exchangeFeesBps}
              onChange={(e) => setExchangeFeesBps(parseFloat(e.target.value) || 1.0)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-900"
            />
          </div>

          <div>
            <label className="block text-gray-500 font-medium mb-1">Slippage (bps)</label>
            <input
              type="number"
              step="0.5"
              value={slippageBps}
              onChange={(e) => setSlippageBps(parseFloat(e.target.value) || 1.5)}
              className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-gray-900"
            />
          </div>
        </div>
      </div>

      {result && (
        <>
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              label="Total Roundtrip Friction"
              value={`Rs ${result.total_roundtrip_cost_inr.toLocaleString()}`}
              subtext={`${result.total_cost_basis_points} bps of total turnover`}
              badge={<Badge variant="gold">COST HURDLE</Badge>}
            />

            <MetricCard
              label="Break-Even Spread Gap"
              value={`${(result.break_even_spread_divergence_pct * 100).toFixed(1)} bps`}
              subtext={`${result.break_even_spread_divergence_pct.toFixed(3)}% divergence needed`}
              className="border-amber-200"
            />

            <MetricCard
              label="Statutory Fees & Taxes"
              value={`Rs ${result.statutory_total_inr.toLocaleString()}`}
              subtext="Exchange, SEBI, Stamp Duty, GST"
            />

            <MetricCard
              label="Microstructure Friction"
              value={`Rs ${(result.bid_ask_cost_inr + result.slippage_cost_inr + result.market_impact_cost_inr).toLocaleString()}`}
              subtext="Bid-ask spread + execution delay"
            />
          </div>

          {/* Detailed Itemized Rupee Breakdown & Sensitivity Matrix */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Itemized Cost Breakdown */}
            <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3">
              <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider border-b border-gray-100 pb-2.5">
                Itemized Rupee Cost Breakdown (4 Legs Roundtrip)
              </h2>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600 font-sans">Total Roundtrip Turnover</span>
                  <span className="font-bold text-gray-900">Rs {result.turnover_inr.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600 font-sans">1. Brokerage Charges</span>
                  <span className="text-gray-900">Rs {result.brokerage_inr.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600 font-sans">2. MCX Exchange Turnover Fees</span>
                  <span className="text-gray-900">Rs {result.exchange_fees_inr.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600 font-sans">3. SEBI Turnover Charges</span>
                  <span className="text-gray-900">Rs {result.sebi_charges_inr.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600 font-sans">4. Stamp Duty (Buy Leg)</span>
                  <span className="text-gray-900">Rs {result.stamp_duty_inr.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600 font-sans">5. GST on Charges (18%)</span>
                  <span className="text-gray-900">Rs {result.gst_inr.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600 font-sans">6. Bid-Ask Spread Crossing</span>
                  <span className="text-gray-900">Rs {result.bid_ask_cost_inr.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-gray-600 font-sans">7. Slippage & Market Impact</span>
                  <span className="text-gray-900">
                    Rs {(result.slippage_cost_inr + result.market_impact_cost_inr).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Right: Sensitivity Matrix */}
            <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3 flex flex-col justify-between">
              <div>
                <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider border-b border-gray-100 pb-2.5 mb-3">
                  Slippage Sensitivity & Break-Even Analysis
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-gray-50 text-gray-500 text-[10px] uppercase border-b border-gray-200">
                      <tr>
                        <th className="py-2 px-3 font-sans">Scenario</th>
                        <th className="py-2 px-3">Slippage</th>
                        <th className="py-2 px-3">Total Cost (INR)</th>
                        <th className="py-2 px-3">Required Spread</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {result.sensitivity_table.map((row, idx) => (
                        <tr key={idx} className="hover:bg-gray-50/70">
                          <td className="py-2 px-3 font-sans font-medium text-gray-800">{row.scenario}</td>
                          <td className="py-2 px-3">{row.slippage_bps} bps</td>
                          <td className="py-2 px-3">Rs {row.total_roundtrip_inr.toLocaleString()}</td>
                          <td className="py-2 px-3 font-bold text-amber-900">{row.break_even_bps} bps</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="text-[11px] text-gray-500 bg-gray-50 border border-gray-200 rounded p-3 leading-relaxed">
                <strong>Model Assumption Disclaimer:</strong> {result.disclaimer}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
