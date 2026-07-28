// Types mirrored from the FastAPI backend contract.
// Backend: FastAPI + Pandas + Plotly + LLM insights API.
// Source of truth: backend/app/routers, backend/app/models (Pydantic schemas).

export interface Dataset {
  id: string;
  filename: string;
  rows: number;
  columns: number;
  size_bytes: number;
  uploaded_at: string;
  status: "processing" | "ready" | "error";
}

export interface UploadResponse {
  id: string;
  filename: string;
  rows: number;
  columns: number;
  size_bytes: number;
  uploaded_at: string;
}

export interface ColumnSummary {
  name: string;
  dtype: string;
  missing_count: number;
  missing_pct: number;
  unique_count: number;
  mean?: number;
  median?: number;
  std?: number;
  min?: number;
  max?: number;
  top_value?: string;
}

export interface DatasetSummary {
  id: string;
  filename: string;
  rows: number;
  columns: number;
  column_summaries: ColumnSummary[];
  preview_rows: Record<string, unknown>[];
  missing_values_total: number;
  duplicate_rows: number;
}

export interface PlotlyFigure {
  data: unknown[];
  layout: Record<string, unknown>;
}

export interface DatasetCharts {
  id: string;
  charts: {
    title: string;
    type: string;
    figure: PlotlyFigure;
  }[];
}

export interface InsightsRequest {
  question?: string;
}

export interface InsightsResponse {
  id: string;
  insights: string;
  generated_at: string;
}

export interface ApiError {
  detail: string;
}
