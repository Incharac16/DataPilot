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

export interface DatasetRecord extends Omit<Dataset, "status"> {
  file_format: string;
  status: Dataset["status"] | "missing";
}

export interface UploadResponse {
  id: string;
  filename: string;
  rows: number;
  columns: number;
  size_bytes: number;
  uploaded_at: string;
  status?: "processing" | "ready" | "error" | "missing";
}

export interface ColumnSummary {
  name: string;
  dtype: string;
  semantic_type: "numeric" | "categorical" | "boolean" | "datetime" | "identifier" | "unknown";
  identifier_reason: string | null;
  missing_count: number;
  missing_pct: number;
  unique_count: number;
  duplicate_value_count: number;
  top_value: string | null;
  top_value_count: number | null;
  top_value_status: "no_values" | "no_repeated_value" | "repeated" | "tie";
  top_value_ties: string[];
  mean: number | null;
  median: number | null;
  std: number | null;
  min: number | null;
  max: number | null;
  true_count: number | null;
  true_pct: number | null;
  false_count: number | null;
  false_pct: number | null;
  earliest: string | null;
  latest: string | null;
  format_issue_count: number;
}

export interface QualityComponent {
  name: string;
  score: number;
  explanation: string;
}

export interface QualityRecommendation {
  issue: string;
  affected_count: number;
  message: string;
}

export interface DataQualitySummary {
  overall_score: number;
  components: QualityComponent[];
  potential_outliers: QualityRecommendation[];
  recommendations: QualityRecommendation[];
}

export interface DatasetSummary {
  id: string;
  filename: string;
  rows: number;
  total_rows: number;
  matching_rows: number;
  current_page: number;
  page_size: number;
  columns: number;
  column_summaries: ColumnSummary[];
  preview_rows: Record<string, unknown>[];
  missing_values_total: number;
  duplicate_rows: number;
  data_quality: DataQualitySummary;
}

export interface DatasetSummaryParams {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: string;
  sort_desc?: boolean;
}

export interface PlotlyFigure {
  data: unknown[];
  layout: Record<string, unknown>;
}

export interface DatasetCharts {
  id: string;
  diagnostics: string[];
  unsupported_charts: {
    type: string;
    reason: string;
  }[];
  available_columns: {
    numeric: string[];
    categorical: string[];
    datetime: string[];
  };
  charts: {
    title: string;
    type: string;
    x_column: string | null;
    y_column: string | null;
    figure: PlotlyFigure;
  }[];
}

export type ChartType = "bar" | "pie" | "histogram" | "line" | "scatter" | "box" | "heatmap";

export interface InsightsRequest {
  question?: string;
}

export interface InsightsResponse {
  id: string;
  insights: string;
  generated_at: string;
  verified_facts: string[];
}

export interface ApiError {
  detail: string;
}
