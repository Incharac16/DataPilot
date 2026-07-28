import { lazy, Suspense } from "react";
import { ChartSkeleton } from "@/components/common/LoadingState";
import type { PlotlyFigure } from "@/types/api";
import { useTheme } from "@/context/ThemeContext";

const Plot = lazy(() => import("react-plotly.js"));

export function PlotlyChart({ figure, title }: { figure: PlotlyFigure; title: string }) {
  const { theme } = useTheme();

  return (
    <Suspense fallback={<ChartSkeleton />}>
      <Plot
        data={figure.data as never}
        layout={{
          ...figure.layout,
          title: undefined,
          autosize: true,
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: theme === "dark" ? "#e5e5e5" : "#171717", family: "Inter, sans-serif" },
          margin: { t: 24, r: 24, b: 40, l: 48 },
        }}
        config={{ responsive: true, displaylogo: false }}
        style={{ width: "100%", height: "360px" }}
        useResizeHandler
        aria-label={title}
      />
    </Suspense>
  );
}
