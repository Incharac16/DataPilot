import { Component, lazy, Suspense } from "react";
import type { ReactNode } from "react";
import { ChartSkeleton } from "@/components/common/LoadingState";
import type { PlotlyFigure } from "@/types/api";
import { useTheme } from "@/context/ThemeContext";

const Plot = lazy(() => import("react-plotly.js"));

class PlotErrorBoundary extends Component<
  { title: string; children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          Could not render “{this.props.title}”: {this.state.error.message || "The chart data could not be displayed."}
        </div>
      );
    }
    return this.props.children;
  }
}

export function PlotlyChart({ figure, title }: { figure: PlotlyFigure; title: string }) {
  const { theme } = useTheme();

  return (
    <PlotErrorBoundary title={title}>
      <div className="h-[340px] min-w-0 max-w-full overflow-hidden">
        <Suspense fallback={<ChartSkeleton />}>
          <Plot
            data={figure.data as never}
            layout={{
              ...figure.layout,
              title: undefined,
              width: undefined,
              height: undefined,
              autosize: true,
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: { color: theme === "dark" ? "#e5e5e5" : "#171717", family: "Inter, sans-serif" },
              margin: { t: 24, r: 24, b: 40, l: 48 },
            }}
            config={{
              responsive: true,
              displayModeBar: true,
              displaylogo: false,
              toImageButtonOptions: {
                format: "png",
                filename: title.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
                scale: 2,
              },
            }}
            style={{ width: "100%", height: "340px" }}
            useResizeHandler
            aria-label={title}
          />
        </Suspense>
      </div>
    </PlotErrorBoundary>
  );
}
