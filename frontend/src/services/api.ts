// Central API client. Every HTTP call in the app goes through here.
// Base URL is read from VITE_BACKEND_URL (see .env.example) so nothing is hardcoded.
// In dev, Vite also proxies /api -> VITE_BACKEND_URL (see vite.config.ts) so a relative
// base of "" works out of the box.

import type {
  DatasetCharts,
  DatasetRecord,
  DatasetSummary,
  DatasetSummaryParams,
  ChartType,
  InsightsRequest,
  InsightsResponse,
  UploadResponse,
} from "@/types/api";

const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? "";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** POST /api/upload — Upload a CSV or XLSX file. */
export function uploadDataset(file: File, onProgress?: (pct: number) => void): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  // Use XHR instead of fetch here so we can report real upload progress.
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE_URL}/api/upload`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new ApiError(xhr.status, "Malformed response from server"));
        }
      } else {
        let detail = xhr.statusText;
        try {
          detail = JSON.parse(xhr.responseText).detail ?? detail;
        } catch {
          // ignore
        }
        reject(new ApiError(xhr.status, detail));
      }
    };

    xhr.onerror = () => reject(new ApiError(0, "Network error during upload"));
    xhr.send(formData);
  });
}

/** GET /api/datasets/{id}/summary — Full-dataset analytics with paginated, searchable preview rows. */
export function getDatasetSummary(
  id: string,
  params: DatasetSummaryParams = {},
): Promise<DatasetSummary> {
  const query = new URLSearchParams();
  if (params.page !== undefined) query.set("page", String(params.page));
  if (params.page_size !== undefined) query.set("page_size", String(params.page_size));
  if (params.search !== undefined) query.set("search", params.search);
  if (params.sort_by !== undefined) query.set("sort_by", params.sort_by);
  if (params.sort_desc !== undefined) query.set("sort_desc", String(params.sort_desc));
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return request<DatasetSummary>(`/api/datasets/${id}/summary${suffix}`);
}

/** GET /api/datasets/{id}/charts — Auto-generated Plotly charts. */
export function getDatasetCharts(
  id: string,
  options?: { chart_type: ChartType; x_column?: string; y_column?: string },
): Promise<DatasetCharts> {
  const query = new URLSearchParams();
  if (options) {
    query.set("chart_type", options.chart_type);
    if (options.x_column) query.set("x_column", options.x_column);
    if (options.y_column) query.set("y_column", options.y_column);
  }
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return request<DatasetCharts>(`/api/datasets/${id}/charts${suffix}`);
}

/** POST /api/datasets/{id}/insights — AI-generated insights for a dataset. */
export function getDatasetInsights(id: string, body: InsightsRequest = {}): Promise<InsightsResponse> {
  return request<InsightsResponse>(`/api/datasets/${id}/insights`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** GET /api/datasets — Persisted upload history. */
export function listDatasets(): Promise<DatasetRecord[]> {
  return request<DatasetRecord[]>("/api/datasets");
}

/** DELETE /api/datasets/{id} — Remove dataset metadata and its stored upload. */
export function deleteDataset(id: string): Promise<void> {
  return request<void>(`/api/datasets/${id}`, { method: "DELETE" });
}

/** GET /api/datasets/{id}/report.pdf — Download a generated PDF report. */
export async function downloadDatasetReport(id: string): Promise<Blob> {
  const response = await fetch(`${BASE_URL}/api/datasets/${encodeURIComponent(id)}/report.pdf`, {
    headers: { Accept: "application/pdf" },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON — retain status text
    }
    throw new ApiError(response.status, detail);
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.toLowerCase().includes("application/pdf")) {
    throw new ApiError(response.status, "The server response was not a PDF file.");
  }

  const blob = await response.blob();
  const signature = new Uint8Array(await blob.slice(0, 5).arrayBuffer());
  if (signature.length !== 5 || String.fromCharCode(...signature) !== "%PDF-") {
    throw new ApiError(response.status, "The server returned an invalid PDF file.");
  }
  return blob;
}

/** Chat UI uses one-shot /insights requests; conversation history is not persisted. */
export function sendChatMessage(...args: [datasetId: string, message: string]): Promise<never> {
  void args;
  throw new ApiError(501, "Chat endpoint is not implemented on the backend yet.");
}

/** Legacy placeholder; the Reports page uses /insights and Analytics exports PDF. */
export function generateReport(...args: [datasetId: string]): Promise<never> {
  void args;
  throw new ApiError(501, "Report generation endpoint is not implemented on the backend yet.");
}

export { ApiError };
