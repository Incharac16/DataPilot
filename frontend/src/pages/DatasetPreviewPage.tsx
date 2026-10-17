import { useState } from "react";
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
import { useDebounce } from "@/hooks/useDebounce";
import { paths } from "@/routes/paths";

export default function DatasetPreviewPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<string | undefined>();
  const [sortDesc, setSortDesc] = useState(false);
  const debouncedSearch = useDebounce(search, 300);
  const { data, isLoading, isError, refetch } = useDatasetSummary(datasetId, {
    page,
    page_size: 10,
    search: debouncedSearch.trim(),
    sort_by: sortBy,
    sort_desc: sortDesc,
  });

  return (
    <div className="min-w-0">
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
        <Card className="min-w-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle>Row preview</CardTitle>
            {data && <Badge variant="secondary">{data.duplicate_rows} duplicate rows</Badge>}
          </CardHeader>
          <CardContent className="min-w-0">
            {isLoading ? (
              <TableSkeleton />
            ) : (
              <DataTable
                rows={data?.preview_rows ?? []}
                columns={data?.column_summaries.map((column) => column.name) ?? []}
                search={search}
                onSearchChange={(value) => {
                  setSearch(value);
                  setPage(1);
                }}
                currentPage={data?.current_page ?? page}
                pageSize={data?.page_size ?? 10}
                matchingRows={data?.matching_rows ?? 0}
                totalRows={data?.total_rows ?? 0}
                onPageChange={setPage}
                sortBy={sortBy}
                sortDesc={sortDesc}
                onSortChange={(column, descending) => {
                  setSortBy(column);
                  setSortDesc(descending);
                  setPage(1);
                }}
              />
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
