import { useParams } from "react-router-dom";
import { PageHeader } from "@/components/common/PageHeader";
import { ColumnSummaryCard } from "@/components/analytics/ColumnSummaryCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CardGridSkeleton } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { useDatasetSummary } from "@/hooks/useDataset";

export default function AnalyticsPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const { data, isLoading, isError, refetch } = useDatasetSummary(datasetId);

  if (isError) {
    return (
      <div>
        <PageHeader title="Analytics" description="Summary statistics and column-level detail." />
        <ErrorState description="Couldn't load analytics for this dataset." onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Analytics"
        description={data ? `Summary statistics across ${data.column_summaries.length} columns` : "Summary statistics and column-level detail."}
      />

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Total rows</p>
            <p className="mt-2 text-2xl font-semibold">{isLoading ? "—" : data?.rows.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Missing values</p>
            <p className="mt-2 text-2xl font-semibold">{isLoading ? "—" : data?.missing_values_total.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Duplicate rows</p>
            <p className="mt-2 text-2xl font-semibold">{isLoading ? "—" : data?.duplicate_rows.toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Column breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <CardGridSkeleton count={6} />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data?.column_summaries.map((col) => (
                <ColumnSummaryCard key={col.name} column={col} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
