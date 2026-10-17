import { useState } from "react";
import { useParams } from "react-router-dom";
import { BarChart3, Download, Table2 } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { ColumnSummaryCard } from "@/components/analytics/ColumnSummaryCard";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CardGridSkeleton, ChartSkeleton } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { useDatasetCharts, useDatasetSummary } from "@/hooks/useDataset";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/button";
import { downloadDatasetReport } from "@/services/api";

const chartTypeLabels: Record<string, string> = {
  bar: "Bar Chart",
  pie: "Pie / Donut Chart",
  histogram: "Histogram",
  line: "Line Chart",
  scatter: "Scatter Plot",
  box: "Box Plot",
  heatmap: "Correlation Heatmap",
};

export default function AnalyticsPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useDatasetSummary(datasetId);
  const {
    data: chartData,
    isLoading: chartsLoading,
    isError: chartsError,
    error: chartError,
    refetch: refetchCharts,
  } = useDatasetCharts(datasetId);

  if (isError) {
    return (
      <div>
        <PageHeader title="Analytics" description="Dataset preview, summary statistics, and visualizations." />
        <ErrorState description="Couldn't load analytics for this dataset." onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title={data?.filename ?? "Dataset analytics"}
        description={data ? `${data.total_rows.toLocaleString()} rows · ${data.columns} columns` : "Dataset preview, summary statistics, and visualizations."}
        actions={
          <Button
            variant="outline"
            disabled={!datasetId || reportLoading || isLoading}
            onClick={async () => {
              if (!datasetId) return;
              setReportLoading(true);
              setReportError(null);
              try {
                const blob = await downloadDatasetReport(datasetId);
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = `${(data?.filename ?? "dataset").replace(/[^a-z0-9_-]+/gi, "-")}-report.pdf`;
                link.hidden = true;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.setTimeout(() => URL.revokeObjectURL(url), 1000);
              } catch (error) {
                setReportError(error instanceof Error ? error.message : "PDF report generation failed.");
              } finally {
                setReportLoading(false);
              }
            }}
          >
            <Download className="h-4 w-4" />
            {reportLoading ? "Generating PDF…" : "Export PDF Report"}
          </Button>
        }
      />
      {reportError && <p role="alert" className="mb-4 text-sm text-destructive">{reportError}</p>}

      <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="min-w-0">
          <CardContent className="min-w-0 p-5">
            <p className="text-sm text-muted-foreground">Total rows</p>
            <p className="mt-2 text-2xl font-semibold">{isLoading ? "—" : data?.total_rows.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className="min-w-0">
          <CardContent className="min-w-0 p-5">
            <p className="text-sm text-muted-foreground">Columns</p>
            <p className="mt-2 text-2xl font-semibold">{isLoading ? "—" : data?.columns.toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="min-w-0">
          <CardContent className="min-w-0 p-5">
            <p className="text-sm text-muted-foreground">Missing values</p>
            <p className="mt-2 text-2xl font-semibold">{isLoading ? "—" : data?.missing_values_total.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className="min-w-0">
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Duplicate rows</p>
            <p className="mt-2 text-2xl font-semibold">{isLoading ? "—" : data?.duplicate_rows.toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      <Card className="min-w-0">
        <CardHeader>
          <CardTitle title="Arithmetic mean of missing-data, duplicate-row, and checked-format component scores.">
            Data quality & trust
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Calculating quality metrics…</p>
          ) : data?.data_quality ? (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center gap-3">
                <Badge variant="secondary">
                  Overall score: {data.data_quality.overall_score.toFixed(1)} / 100
                </Badge>
                <p className="text-xs text-muted-foreground">
                  Deterministic rule-based score; potential outliers are reported separately and do not reduce the score.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {data.data_quality.components.map((component) => (
                  <div key={component.name} className="min-w-0 rounded-lg border border-border p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium">{component.name}</span>
                      <span className="text-sm font-semibold">{component.score.toFixed(1)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground" title={component.explanation}>
                      {component.explanation}
                    </p>
                  </div>
                ))}
              </div>
              {(data.data_quality.recommendations.length > 0 || data.data_quality.potential_outliers.length > 0) && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">Review recommendations</h3>
                  {[...data.data_quality.recommendations, ...data.data_quality.potential_outliers].map((item, index) => (
                    <p key={`${item.issue}-${index}`} className="break-words text-sm text-muted-foreground">
                      <span className="font-medium text-foreground">{item.affected_count.toLocaleString()} · </span>
                      {item.message}
                    </p>
                  ))}
                </div>
              )}
              {data.data_quality.recommendations.length === 0 && data.data_quality.potential_outliers.length === 0 && (
                <p className="text-sm text-muted-foreground">No issues detected by these checks.</p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No quality metrics are available for this dataset.</p>
          )}
        </CardContent>
      </Card>

      <Card className="min-w-0">
        <CardHeader>
          <CardTitle>Column breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <CardGridSkeleton count={6} />
          ) : data?.column_summaries.length === 0 ? (
            <EmptyState
              icon={Table2}
              title="No columns to profile"
              description="This dataset has no rows or columns available for statistical profiling."
            />
          ) : (
            <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data?.column_summaries.map((col) => (
                <ColumnSummaryCard key={col.name} column={col} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <section aria-labelledby="charts-heading" className="min-w-0 space-y-4">
        <div>
          <h2 id="charts-heading" className="text-xl font-semibold">Charts and Visualizations</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Charts are generated automatically from suitable columns in this dataset.
          </p>
        </div>

        {chartsError && (
          <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
            <p className="font-medium">Charts could not be generated.</p>
            <p className="mt-1">{chartError instanceof Error ? chartError.message : "The server returned an unexpected chart-generation error."}</p>
            <button className="mt-2 underline" onClick={() => refetchCharts()}>Retry</button>
          </div>
        )}

        {chartsLoading && !chartsError && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ChartSkeleton />
            <ChartSkeleton />
          </div>
        )}

        {!chartsLoading && !chartsError && chartData && (
          <>
            {chartData.charts.length > 0 ? (
              <div className="grid min-w-0 grid-cols-1 gap-6 lg:grid-cols-2">
                {chartData.charts.map((chart, index) => (
                  <Card key={`${chart.type}-${chart.title}-${index}`} className="min-w-0 overflow-hidden">
                    <CardHeader className="min-w-0 items-start space-y-2">
                      <Badge variant="secondary">
                        {chartTypeLabels[chart.type] ?? chart.type.replaceAll("_", " ")}
                      </Badge>
                      <CardTitle className="min-w-0 break-words text-base">
                        {chart.title}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="min-w-0 overflow-hidden">
                      <PlotlyChart figure={chart.figure} title={chart.title} />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4">
                <BarChart3 className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  No suitable charts could be generated for this dataset. Try uploading data containing numerical measurements, categorical columns, or date/time values.
                </p>
              </div>
            )}

            {chartData.unsupported_charts.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Charts that could not be generated</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    {chartData.unsupported_charts.map((chart) => (
                      <li key={chart.type}>
                        <span className="font-medium text-foreground">{chart.type}:</span> {chart.reason}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </section>
    </div>
  );
}
