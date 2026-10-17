import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getDatasetCharts, getDatasetInsights, getDatasetSummary, uploadDataset } from "@/services/api";
import type { DatasetSummaryParams, InsightsRequest } from "@/types/api";
import { useState } from "react";

export function useDatasetSummary(
  id: string | undefined,
  params: DatasetSummaryParams = {},
) {
  return useQuery({
    queryKey: ["dataset-summary", id, params],
    queryFn: () => getDatasetSummary(id as string, params),
    enabled: Boolean(id),
  });
}

export function useDatasetCharts(id: string | undefined) {
  return useQuery({
    queryKey: ["dataset-charts", id],
    queryFn: () => getDatasetCharts(id as string),
    enabled: Boolean(id),
  });
}

export function useDatasetInsights(id: string | undefined) {
  return useMutation({
    mutationFn: (body: InsightsRequest = {}) => getDatasetInsights(id as string, body),
  });
}

export function useUploadDataset() {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);

  const mutation = useMutation({
    mutationFn: (file: File) => uploadDataset(file, setProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dataset-summary"] });
      setProgress(0);
    },
    onError: () => setProgress(0),
  });

  return { ...mutation, progress };
}
