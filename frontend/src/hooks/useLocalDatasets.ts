// The backend has no dataset-listing endpoint yet, so recently uploaded/viewed
// datasets are tracked client-side (localStorage) to power the Dashboard and
// History pages. Once GET /api/datasets exists server-side, swap this out.
import { useCallback, useEffect, useState } from "react";
import type { UploadResponse } from "@/types/api";

const STORAGE_KEY = "datapilot-recent-datasets";
const MAX_ITEMS = 25;

export function useLocalDatasets() {
  const [datasets, setDatasets] = useState<UploadResponse[]>([]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) setDatasets(JSON.parse(raw));
    } catch {
      setDatasets([]);
    }
  }, []);

  const addDataset = useCallback((dataset: UploadResponse) => {
    setDatasets((prev) => {
      const next = [dataset, ...prev.filter((d) => d.id !== dataset.id)].slice(0, MAX_ITEMS);
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clearDatasets = useCallback(() => {
    window.localStorage.removeItem(STORAGE_KEY);
    setDatasets([]);
  }, []);

  return { datasets, addDataset, clearDatasets };
}
