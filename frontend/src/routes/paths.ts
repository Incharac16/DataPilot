export const paths = {
  home: "/",
  dashboard: "/dashboard",
  upload: "/upload",
  datasetPreview: (id = ":datasetId") => `/datasets/${id}`,
  analytics: (id = ":datasetId") => `/datasets/${id}/analytics`,
  charts: (id = ":datasetId") => `/datasets/${id}/charts`,
  chat: (id = ":datasetId") => `/datasets/${id}/chat`,
  reports: (id = ":datasetId") => `/datasets/${id}/reports`,
  history: "/history",
  settings: "/settings",
} as const;
