import { useParams } from "react-router-dom";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { ChartSkeleton } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { useDatasetCharts } from "@/hooks/useDataset";
import { LineChart } from "lucide-react";

export default function ChartsPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const { data, isLoading, isError, refetch } = useDatasetCharts(datasetId);

  return (
    <div>
      <PageHeader title="Charts" description="Auto-generated visualizations for this dataset." />

      {isError && <ErrorState description="Couldn't load charts for this dataset." onRetry={() => refetch()} />}

      {!isError && isLoading && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      )}

      {!isError && !isLoading && (data?.charts.length ?? 0) === 0 && (
        <EmptyState icon={LineChart} title="No charts available" description="This dataset didn't produce any auto-generated charts." />
      )}

      {!isError && !isLoading && (data?.charts.length ?? 0) > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {data?.charts.map((chart, i) => (
            <Card key={i}>
              <CardHeader>
                <CardTitle className="text-sm">{chart.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <PlotlyChart figure={chart.figure} title={chart.title} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
