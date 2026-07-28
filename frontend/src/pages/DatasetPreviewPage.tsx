import { useParams, Link } from "react-router-dom";
import { BarChart3, MessageSquare } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable } from "@/components/analytics/DataTable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TableSkeleton } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { useDatasetSummary } from "@/hooks/useDataset";
import { paths } from "@/routes/paths";

export default function DatasetPreviewPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const { data, isLoading, isError, refetch } = useDatasetSummary(datasetId);

  return (
    <div>
      <PageHeader
        title={data?.filename ?? "Dataset preview"}
        description={data ? `${data.rows.toLocaleString()} rows · ${data.columns} columns` : undefined}
        actions={
          datasetId && (
            <>
              <Button asChild variant="outline">
                <Link to={paths.analytics(datasetId)}>
                  <BarChart3 className="h-4 w-4" />
                  Analytics
                </Link>
              </Button>
              <Button asChild>
                <Link to={paths.chat(datasetId)}>
                  <MessageSquare className="h-4 w-4" />
                  Ask AI
                </Link>
              </Button>
            </>
          )
        }
      />

      {isError && <ErrorState description="Couldn't load this dataset's preview." onRetry={() => refetch()} />}

      {!isError && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle>Row preview</CardTitle>
            {data && <Badge variant="secondary">{data.duplicate_rows} duplicate rows</Badge>}
          </CardHeader>
          <CardContent>
            {isLoading ? <TableSkeleton /> : <DataTable rows={data?.preview_rows ?? []} />}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
