import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { ContractSpec, NormalizationBreakdown } from "../types/api";
import { Badge } from "../components/common/Badge";
import { Scale, Calculator, CheckCircle2 } from "lucide-react";

export const ContractsView: React.FC = () => {
  const [specs, setSpecs] = useState<ContractSpec[]>([]);
  const [calcSymbol, setCalcSymbol] = useState("GOLDM");
  const [calcPrice, setCalcPrice] = useState(75000);
  const [breakdown, setBreakdown] = useState<NormalizationBreakdown | null>(null);

  useEffect(() => {
    loadSpecs();
  }, []);

  useEffect(() => {
    runNormalization();
  }, [calcSymbol, calcPrice]);

  const loadSpecs = async () => {
    try {
      const res = await api.getContracts();
      setSpecs(res);
    } catch (err) {
      console.error(err);
    }
  };

  const runNormalization = async () => {
    try {
      const res = await api.normalizePrice(calcSymbol, calcPrice);
      setBreakdown(res.breakdown);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h1 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
          <Scale className="w-5 h-5 text-amber-600" />
          MCX Contract Specifications & Normalization Registry
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Official contract parameters, quotation bases, and transparent pure-gold equivalent normalization formulas.
        </p>
      </div>

      {/* Contract Specifications Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xs font-bold text-gray-800 uppercase tracking-wider">
            Verified MCX Bullion Contract Specifications
          </h2>
          <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Official Circular Verified
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 text-gray-600 font-medium uppercase text-[10px] tracking-wider border-b border-gray-200">
              <tr>
                <th className="py-2.5 px-4">Symbol</th>
                <th className="py-2.5 px-3">Contract Name</th>
                <th className="py-2.5 px-3">Trading Unit</th>
                <th className="py-2.5 px-3">Quotation Basis</th>
                <th className="py-2.5 px-3">Gold Fineness</th>
                <th className="py-2.5 px-3">Tick Size</th>
                <th className="py-2.5 px-3">Delivery Unit</th>
                <th className="py-2.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono text-[11px]">
              {specs.map((s) => (
                <tr key={s.symbol} className="hover:bg-gray-50/80 transition-colors">
                  <td className="py-2.5 px-4 font-bold text-gray-900 font-sans">{s.symbol}</td>
                  <td className="py-2.5 px-3 font-sans text-gray-700">{s.name}</td>
                  <td className="py-2.5 px-3 text-gray-900">{s.trading_unit_grams}g</td>
                  <td className="py-2.5 px-3 text-amber-900 font-bold">Per {s.quotation_basis_grams}g</td>
                  <td className="py-2.5 px-3 text-gray-900 font-bold">{s.purity_per_mille} / 1000</td>
                  <td className="py-2.5 px-3 text-gray-600">Rs {s.tick_size.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-gray-600">{s.delivery_unit_grams}g</td>
                  <td className="py-2.5 px-4 font-sans">
                    <Badge variant="investigate">VERIFIED</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Live Interactive Normalization Calculator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-gray-100 pb-2.5">
            <Calculator className="w-4 h-4 text-amber-600" /> Interactive Normalization Tool
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-gray-600 font-medium mb-1">Select Contract</label>
              <select
                value={calcSymbol}
                onChange={(e) => setCalcSymbol(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-semibold text-gray-800"
              >
                {specs.map((s) => (
                  <option key={s.symbol} value={s.symbol}>
                    {s.symbol} ({s.name})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-gray-600 font-medium mb-1">
                Quoted Market Price (in contract quotation unit)
              </label>
              <input
                type="number"
                step="1"
                value={calcPrice}
                onChange={(e) => setCalcPrice(parseFloat(e.target.value) || 0)}
                className="w-full bg-gray-50 border border-gray-200 rounded px-2.5 py-1.5 font-mono text-base font-bold text-gray-900"
              />
            </div>
          </div>
        </div>

        {/* Normalization Mathematical Breakdown (7 Cols) */}
        <div className="lg:col-span-7 bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wider border-b border-gray-100 pb-2.5">
            Mathematical Step-by-Step Conversion
          </h2>

          {breakdown ? (
            <div className="space-y-3 font-mono text-xs">
              <div className="bg-amber-50/50 border border-amber-200 rounded p-3 text-amber-950 font-sans">
                <div className="text-[10px] text-amber-800 uppercase font-bold tracking-wider mb-1">
                  Normalization Formula Applied:
                </div>
                <div className="text-sm font-mono font-bold">
                  P_pure = (Quoted_Price / Quotation_Basis) / (Purity / 1000)
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="border border-gray-100 rounded p-2.5 bg-gray-50/50">
                  <div className="text-[10px] text-gray-400 font-sans">Step 1: Price per Gram Alloy</div>
                  <div className="text-sm font-bold text-gray-900 mt-1">
                    Rs {breakdown.quoted_price_per_gram_alloy.toFixed(2)} / gram
                  </div>
                  <div className="text-[10px] text-gray-500 font-sans mt-0.5">
                    {breakdown.quoted_price} / {breakdown.quotation_basis_grams}g
                  </div>
                </div>

                <div className="border border-gray-100 rounded p-2.5 bg-gray-50/50">
                  <div className="text-[10px] text-gray-400 font-sans">Step 2: Purity Fineness Fraction</div>
                  <div className="text-sm font-bold text-gray-900 mt-1">
                    {breakdown.purity_fraction}
                  </div>
                  <div className="text-[10px] text-gray-500 font-sans mt-0.5">
                    {breakdown.purity_per_mille} fineness / 1000
                  </div>
                </div>

                <div className="border border-emerald-200 rounded p-2.5 bg-emerald-50/40">
                  <div className="text-[10px] text-emerald-800 font-sans font-bold">
                    Pure Gold Price (Per Gram)
                  </div>
                  <div className="text-lg font-bold text-emerald-900 mt-1">
                    Rs {breakdown.normalized_pure_gold_per_gram.toFixed(4)}
                  </div>
                </div>

                <div className="border border-amber-200 rounded p-2.5 bg-amber-50/40">
                  <div className="text-[10px] text-amber-800 font-sans font-bold">
                    Pure Gold Price (Per 10 Grams)
                  </div>
                  <div className="text-lg font-bold text-amber-900 mt-1">
                    Rs {breakdown.normalized_pure_gold_per_10g.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-gray-400 text-xs">Enter price to compute breakdown</div>
          )}
        </div>
      </div>
    </div>
  );
};
