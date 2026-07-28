// Central API client. Every HTTP call in the app goes through here.
// Base URL is read from VITE_BACKEND_URL (see .env.example) so nothing is hardcoded.
// In dev, Vite also proxies /api -> VITE_BACKEND_URL (see vite.config.ts) so a relative
// base of "" works out of the box.

import type {
  DatasetCharts,
  DatasetSummary,
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

// ---------------------------------------------------------------------------
// Confirmed endpoints (from backend README / routers)
// ---------------------------------------------------------------------------

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

/** GET /api/datasets/{id}/summary — Dataset summary & stats. */
export function getDatasetSummary(id: string): Promise<DatasetSummary> {
  return request<DatasetSummary>(`/api/datasets/${id}/summary`);
}

/** GET /api/datasets/{id}/charts — Auto-generated Plotly charts. */
export function getDatasetCharts(id: string): Promise<DatasetCharts> {
  return request<DatasetCharts>(`/api/datasets/${id}/charts`);
}

/** POST /api/datasets/{id}/insights — AI-generated insights for a dataset. */
export function getDatasetInsights(id: string, body: InsightsRequest = {}): Promise<InsightsResponse> {
  return request<InsightsResponse>(`/api/datasets/${id}/insights`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// TODO — not present in the current backend.
// These are typed placeholders so the UI compiles and runs end-to-end today.
// Wire them up once the corresponding FastAPI routes exist; do not treat the
// paths below as real until confirmed against backend/app/routers.
// ---------------------------------------------------------------------------

/** TODO: no dataset-listing endpoint exists yet (needed for Dashboard/History). */
export function listDatasets(): Promise<never> {
  throw new ApiError(501, "GET /api/datasets is not implemented on the backend yet.");
}

/** TODO: no chat/conversation endpoint exists yet — only one-shot /insights. */
export function sendChatMessage(_datasetId: string, _message: string): Promise<never> {
  throw new ApiError(501, "Chat endpoint is not implemented on the backend yet.");
}

/** TODO: no report generation/export endpoint exists yet. */
export function generateReport(_datasetId: string): Promise<never> {
  throw new ApiError(501, "Report generation endpoint is not implemented on the backend yet.");
}

export { ApiError };
