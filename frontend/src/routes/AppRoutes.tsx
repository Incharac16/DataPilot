import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { Skeleton } from "@/components/ui/skeleton";

const LandingPage = lazy(() => import("@/pages/LandingPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const UploadPage = lazy(() => import("@/pages/UploadPage"));
const DatasetPreviewPage = lazy(() => import("@/pages/DatasetPreviewPage"));
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage"));
const ChartsPage = lazy(() => import("@/pages/ChartsPage"));
const ChatPage = lazy(() => import("@/pages/ChatPage"));
const ReportsPage = lazy(() => import("@/pages/ReportsPage"));
const HistoryPage = lazy(() => import("@/pages/HistoryPage"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

function PageFallback() {
  return (
    <div className="space-y-4 p-2">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/datasets/:datasetId" element={<DatasetPreviewPage />} />
          <Route path="/datasets/:datasetId/analytics" element={<AnalyticsPage />} />
          <Route path="/datasets/:datasetId/charts" element={<ChartsPage />} />
          <Route path="/datasets/:datasetId/chat" element={<ChatPage />} />
          <Route path="/datasets/:datasetId/reports" element={<ReportsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
