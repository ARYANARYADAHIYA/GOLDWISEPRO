import { useState, useEffect } from "react";
import { api } from "./services/api";
import type { AnomalyCandidate } from "./types/api";
import { Badge } from "./components/common/Badge";
import {
  LayoutDashboard, LineChart, Activity, FileSearch, Bookmark,
  Award, TrendingUp, ShieldCheck, DollarSign, GitCompare,
  Calendar, Database, FileText, Settings, Menu, X, ChevronRight
} from "lucide-react";

import { OverviewView } from "./views/OverviewView";
import { MarketExplorerView } from "./views/MarketExplorerView";
import { ScannerView } from "./views/ScannerView";
import { AutopsyView } from "./views/AutopsyView";
import { CasebookView } from "./views/CasebookView";
import { ModelLabView } from "./views/ModelLabView";
import { BacktestView } from "./views/BacktestView";
import { RealityCheckView } from "./views/RealityCheckView";
import { CostSimulatorView } from "./views/CostSimulatorView";
import { CounterfactualView } from "./views/CounterfactualView";
import { LifecycleView } from "./views/LifecycleView";
import { DataCenterView } from "./views/DataCenterView";
import { ReportsAuditView } from "./views/ReportsAuditView";
import { SettingsView } from "./views/SettingsView";

export function App() {
  const [currentView, setCurrentView] = useState("overview");
  const [selectedCandidate, setSelectedCandidate] = useState<AnomalyCandidate | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    checkHealth();
  }, [currentView]);

  const checkHealth = async () => {
    try {
      const res = await api.getHealth();
      setHealth(res);
    } catch (e) {
      console.error("Health check error", e);
    }
  };

  // Exactly 14 QUANTARA-inspired modules for GOLDWISE PRO
  const navSections = [
    {
      title: "Core Surveillance",
      items: [
        { id: "overview", label: "Overview", icon: LayoutDashboard },
        { id: "explorer", label: "Market Explorer", icon: LineChart },
        { id: "scanner", label: "Relative-Value Scanner", icon: Activity },
        { id: "destroyer", label: "Opportunity Destroyer", icon: ShieldCheck },
        { id: "evidence", label: "Signal Evidence", icon: FileSearch },
      ]
    },
    {
      title: "Quantitative Research Lab",
      items: [
        { id: "backtest", label: "Backtesting Lab", icon: TrendingUp },
        { id: "costs", label: "Cost Survival Simulator", icon: DollarSign },
        { id: "lifecycle", label: "Contract Lifecycle", icon: Calendar },
        { id: "workbench", label: "Research Workbench", icon: Bookmark },
        { id: "stress", label: "Stress Testing", icon: GitCompare },
      ]
    },
    {
      title: "Data & Machine Learning",
      items: [
        { id: "datacenter", label: "Data Center", icon: Database },
        { id: "models", label: "Model Lab", icon: Award },
        { id: "reports", label: "Reports & Audit", icon: FileText },
        { id: "settings", label: "Settings", icon: Settings },
      ]
    }
  ];

  const allNavItems = navSections.flatMap((s) => s.items);

  return (
    <div className="min-h-screen bg-[#fbfbfb] text-gray-900 flex flex-col font-sans selection:bg-amber-100 selection:text-amber-900">
      {/* Top QUANTARA Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30 px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-md hover:bg-gray-100 text-gray-600 lg:hidden"
            aria-label="Toggle Navigation Menu"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div
            onClick={() => setCurrentView("overview")}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <div className="w-7 h-7 rounded bg-gray-900 flex items-center justify-center font-bold text-amber-400 text-sm shadow-xs group-hover:scale-105 transition-transform">
              G
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-sm tracking-tight text-gray-900 group-hover:text-amber-700 transition">
                  GOLDWISE PRO
                </span>
                <span className="text-[10px] bg-amber-50 text-amber-800 border border-amber-200/80 font-mono px-1.5 py-0.2 rounded font-semibold">
                  MCX Terminal
                </span>
              </div>
              <div className="text-[10px] text-gray-400 font-mono hidden sm:block">
                Institutional Gold Relative-Value & Anomaly Investigation
              </div>
            </div>
          </div>
        </div>

        {/* Global Dataset Status & System Health */}
        <div className="flex items-center gap-3 text-xs">
          {health && (
            <Badge variant={health.dataset_type === "SYNTHETIC" ? "synthetic" : "real"}>
              {health.dataset_type === "SYNTHETIC"
                ? "Synthetic Reference Mode"
                : "Live MCX Bhavcopy Active"}
            </Badge>
          )}

          <div className="hidden md:flex items-center gap-1.5 text-gray-500 font-mono text-[11px] bg-gray-50 border border-gray-200 px-2 py-0.5 rounded">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>ONLINE</span>
          </div>

          <button
            onClick={() => setCurrentView("settings")}
            className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded transition"
            title="Settings & System Configuration"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Layout Container */}
      <div className="flex flex-1">
        {/* Persistent Left Navigation Sidebar */}
        <aside
          className={`fixed lg:sticky top-12 left-0 z-20 h-[calc(100vh-48px)] w-64 bg-white border-r border-gray-200 flex flex-col justify-between py-3 transition-transform duration-200 ease-in-out ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
          }`}
        >
          <div className="px-3 space-y-4 overflow-y-auto">
            {navSections.map((sec, idx) => (
              <div key={idx} className="space-y-1">
                <div className="px-3 py-1 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  {sec.title}
                </div>
                {sec.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentView === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        setCurrentView(item.id);
                        setSidebarOpen(false);
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-semibold transition-colors ${
                        isActive
                          ? "bg-gray-900 text-white shadow-xs"
                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? "text-amber-400" : "text-gray-400"}`} />
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Sidebar Footer */}
          <div className="px-4 pt-3 border-t border-gray-100 text-[11px] text-gray-400 font-mono space-y-1">
            <div className="flex items-center justify-between">
              <span>MCX Bullion:</span>
              <span className="text-emerald-700 font-bold">VERIFIED</span>
            </div>
            <div className="text-[10px] text-gray-400">GOLD &bull; GOLDM &bull; GOLDTEN &bull; GUINEA &bull; PETAL</div>
          </div>
        </aside>

        {/* Content View Router */}
        <main className="flex-1 overflow-x-hidden min-h-[calc(100vh-48px)] bg-[#fbfbfb]">
          {/* Breadcrumb strip */}
          <div className="bg-white border-b border-gray-100 px-6 py-2 text-xs text-gray-500 flex items-center justify-between font-mono">
            <div className="flex items-center gap-1.5">
              <span>GOLDWISE PRO</span>
              <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-900 font-bold font-sans">
                {allNavItems.find((n) => n.id === currentView)?.label}
              </span>
            </div>

            <div className="text-[11px] text-gray-400 font-sans hidden sm:block">
              Quotation Basis: INR / Pure Gram Reference
            </div>
          </div>

          {/* 1. Overview */}
          {currentView === "overview" && (
            <OverviewView
              onNavigate={(viewId) => {
                if (viewId === "scanner") setCurrentView("scanner");
                else if (viewId === "explorer") setCurrentView("explorer");
                else if (viewId === "datacenter") setCurrentView("datacenter");
                else if (viewId === "models") setCurrentView("models");
                else if (viewId === "backtest") setCurrentView("backtest");
                else setCurrentView(viewId);
              }}
              onSelectCandidate={(_candId) => {
                setCurrentView("scanner");
              }}
            />
          )}

          {/* 2. Market Explorer */}
          {currentView === "explorer" && <MarketExplorerView />}

          {/* 3. Relative-Value Scanner */}
          {currentView === "scanner" && (
            <ScannerView
              onInspectAutopsy={(cand) => {
                setSelectedCandidate(cand);
                setCurrentView("evidence");
              }}
              onInspectCounterfactual={(cand) => {
                setSelectedCandidate(cand);
                setCurrentView("stress");
              }}
              onAddToCasebook={(cand) => {
                setSelectedCandidate(cand);
                setCurrentView("workbench");
              }}
            />
          )}

          {/* 4. Opportunity Destroyer (Reality Check) */}
          {currentView === "destroyer" && <RealityCheckView />}

          {/* 5. Signal Evidence (Signal Autopsy) */}
          {currentView === "evidence" && (
            <AutopsyView
              candidate={selectedCandidate}
              onBack={() => setCurrentView("scanner")}
              onNavigateToCasebook={(cand) => {
                setSelectedCandidate(cand);
                setCurrentView("workbench");
              }}
            />
          )}

          {/* 6. Backtesting Lab */}
          {currentView === "backtest" && <BacktestView />}

          {/* 7. Cost Survival Simulator */}
          {currentView === "costs" && <CostSimulatorView />}

          {/* 8. Contract Lifecycle */}
          {currentView === "lifecycle" && <LifecycleView />}

          {/* 9. Research Workbench (Casebook) */}
          {currentView === "workbench" && <CasebookView />}

          {/* 10. Stress Testing (Counterfactual) */}
          {currentView === "stress" && (
            <CounterfactualView initialCandidate={selectedCandidate} />
          )}

          {/* 11. Data Center */}
          {currentView === "datacenter" && <DataCenterView />}

          {/* 12. Model Lab */}
          {currentView === "models" && <ModelLabView />}

          {/* 13. Reports & Audit */}
          {currentView === "reports" && <ReportsAuditView />}

          {/* 14. Settings */}
          {currentView === "settings" && <SettingsView />}
        </main>
      </div>
    </div>
  );
}

export default App;
