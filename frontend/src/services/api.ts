import type {
  ContractSpec, NormalizationBreakdown, DatasetSummary, ScanResponse,
  AnomalyCandidate, ExecutiveOverview, BacktestResult, CostSimulationResult,
  RealityCheckResult, MLModelRecord, TournamentResult, PaperResearchRecord,
  LifecycleItem, RegimeAnalysisResult, DataIntegrityReport
} from "../types/api";

const API_BASE = "/api";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    let errorDetail = `HTTP Error ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {}
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  getHealth: () => fetchJson<{ status: string; database_connected: boolean; active_dataset_id: string; dataset_type: string; total_datasets: number }>("/health"),
  getOverview: () => fetchJson<ExecutiveOverview>("/overview"),
  getContracts: () => fetchJson<ContractSpec[]>("/contracts"),
  normalizePrice: (symbol: string, quoted_price: number) =>
    fetchJson<{ breakdown: NormalizationBreakdown }>("/contracts/normalize", {
      method: "POST",
      body: JSON.stringify({ symbol, quoted_price }),
    }),

  getDatasets: () => fetchJson<DatasetSummary[]>("/datasets"),
  activateDataset: (datasetId: string) =>
    fetchJson<{ message: string; dataset_id: string }>(`/datasets/${datasetId}/activate`, {
      method: "POST",
    }),

  uploadCsv: async (file: File, name: string, description?: string, dateFormat: string = "DD/MM/YYYY") => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("dataset_name", name);
    if (description) formData.append("description", description);
    formData.append("preferred_date_format", dateFormat);

    const res = await fetch(`${API_BASE}/datasets/import`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "CSV upload failed");
    }
    return res.json();
  },

  getMarketExplorer: (symbolA = "GOLDM", symbolB = "GOLD", datasetId?: string) => {
    const q = new URLSearchParams({ symbol_a: symbolA, symbol_b: symbolB });
    if (datasetId) q.append("dataset_id", datasetId);
    return fetchJson<{ dataset_id: string; symbol_a: string; symbol_b: string; total_points: number; series: any[] }>(
      `/market-explorer?${q.toString()}`
    );
  },

  runScan: (params: {
    dataset_id: string;
    pair_symbol_a?: string;
    pair_symbol_b?: string;
    zscore_threshold?: number;
    rolling_window_days?: number;
    slippage_bps?: number;
    brokerage_bps?: number;
    expiry_buffer_days?: number;
  }) => fetchJson<ScanResponse>("/scans/run", { method: "POST", body: JSON.stringify(params) }),

  getCandidateDetails: (candidateId: string) =>
    fetchJson<AnomalyCandidate>(`/candidates/${candidateId}`),

  trainModel: (params: {
    name: string;
    model_type: string;
    dataset_id: string;
    contamination?: number;
    n_estimators?: number;
  }) => fetchJson<MLModelRecord>("/models/train", { method: "POST", body: JSON.stringify(params) }),

  getModels: () => fetchJson<MLModelRecord[]>("/models"),
  getTournament: (datasetId?: string) => {
    const q = datasetId ? `?dataset_id=${datasetId}` : "";
    return fetchJson<TournamentResult>(`/tournament${q}`);
  },

  getDrift: (datasetId?: string) => {
    const q = datasetId ? `?dataset_id=${datasetId}` : "";
    return fetchJson<any>(`/drift${q}`);
  },

  runBacktest: (params: {
    dataset_id: string;
    pair_symbol_a?: string;
    pair_symbol_b?: string;
    entry_zscore?: number;
    exit_zscore?: number;
    holding_period_days?: number;
    position_size_inr?: number;
    slippage_bps?: number;
    execution_delay_days?: number;
  }) => fetchJson<BacktestResult>("/backtests/run", { method: "POST", body: JSON.stringify(params) }),

  runCostSimulation: (params: {
    quoted_price_per_10g?: number;
    contract_lot_grams?: number;
    position_lots?: number;
    brokerage_bps?: number;
    exchange_fees_bps?: number;
    slippage_bps?: number;
  }) => fetchJson<CostSimulationResult>("/cost-simulator", { method: "POST", body: JSON.stringify(params) }),

  runRealityCheck: (params: {
    dataset_id: string;
    pair_symbol_a?: string;
    pair_symbol_b?: string;
    rolling_windows?: number[];
    zscore_thresholds?: number[];
  }) => fetchJson<RealityCheckResult>("/reality-check", { method: "POST", body: JSON.stringify(params) }),

  runCounterfactual: (params: {
    candidate_id: string;
    modified_slippage_bps?: number;
    modified_zscore_threshold?: number;
    modified_expiry_buffer_days?: number;
  }) => fetchJson<any>("/counterfactual", { method: "POST", body: JSON.stringify(params) }),

  getLifecycle: (datasetId?: string) => {
    const q = datasetId ? `?dataset_id=${datasetId}` : "";
    return fetchJson<{ contracts: LifecycleItem[]; roll_schedule_summary: string }>(`/lifecycle${q}`);
  },

  getRegime: (datasetId?: string) => {
    const q = datasetId ? `?dataset_id=${datasetId}` : "";
    return fetchJson<RegimeAnalysisResult>(`/regime${q}`);
  },

  getIntegrity: (datasetId?: string) => {
    const q = datasetId ? `?dataset_id=${datasetId}` : "";
    return fetchJson<DataIntegrityReport>(`/integrity${q}`);
  },

  getCasebook: () => fetchJson<PaperResearchRecord[]>("/casebook"),
  createCasebook: (params: {
    candidate_id?: string;
    symbol_pair: string;
    observation_date: string;
    initial_verdict: string;
    spread_bps: number;
    rationale: string;
    entry_price_spread: number;
  }) => fetchJson<PaperResearchRecord>("/casebook", { method: "POST", body: JSON.stringify(params) }),

  getAudit: (limit = 40) => fetchJson<any[]>(`/audit?limit=${limit}`),
  generateReport: (datasetId?: string) => {
    const q = datasetId ? `?dataset_id=${datasetId}` : "";
    return fetchJson<{ report_id: string; timestamp: string; markdown_content: string; file_path: string }>(
      `/reports/generate${q}`,
      { method: "POST" }
    );
  },

  getSettings: () => fetchJson<any>("/settings"),
  updateSetting: (key: string, value: string) =>
    fetchJson<any>(`/settings?key=${encodeURIComponent(key)}&value=${encodeURIComponent(value)}`, {
      method: "POST",
    }),

  getDataCollectionStatus: () => fetchJson<any>("/data/collection-status"),
  collectMcx: (targetDate?: string) =>
    fetchJson<any>(`/data/collect-mcx${targetDate ? `?target_date=${targetDate}` : ""}`, {
      method: "POST",
    }),
  seedRealMcx: () => fetchJson<any>("/data/seed-real-mcx", { method: "POST" }),

  getForecast: (datasetId?: string) => {
    const q = datasetId ? `?dataset_id=${datasetId}` : "";
    return fetchJson<any>(`/forecast${q}`);
  },

  retrainModels: (datasetId?: string, force: boolean = true) => {
    const q = new URLSearchParams({ force: String(force) });
    if (datasetId) q.append("dataset_id", datasetId);
    return fetchJson<any>(`/models/retrain?${q.toString()}`, { method: "POST" });
  },
};
