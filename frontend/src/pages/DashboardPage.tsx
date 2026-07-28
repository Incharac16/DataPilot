import { Link } from "react-router-dom";
import { Database, FileSpreadsheet, Rows3, Upload as UploadIcon } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { RecentDatasetsTable } from "@/components/dashboard/RecentDatasetsTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLocalDatasets } from "@/hooks/useLocalDatasets";
import { paths } from "@/routes/paths";

export default function DashboardPage() {
  const { datasets } = useLocalDatasets();

  const totalRows = datasets.reduce((sum, d) => sum + d.rows, 0);
  const totalColumns = datasets.reduce((sum, d) => sum + d.columns, 0);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="An overview of your recent datasets and activity."
        actions={
          <Button asChild>
            <Link to={paths.upload}>
              <UploadIcon className="h-4 w-4" />
              Upload dataset
            </Link>
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Datasets uploaded" value={String(datasets.length)} icon={Database} />
        <KpiCard label="Total rows analyzed" value={totalRows.toLocaleString()} icon={Rows3} />
        <KpiCard label="Total columns" value={totalColumns.toLocaleString()} icon={FileSpreadsheet} />
        <KpiCard label="Most recent" value={datasets[0]?.filename ?? "—"} icon={UploadIcon} />
      </div>

      <Card className="mt-6">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Recent datasets</CardTitle>
          {datasets.length > 0 && (
            <Button asChild variant="ghost" size="sm">
              <Link to={paths.history}>View all</Link>
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <RecentDatasetsTable datasets={datasets.slice(0, 5)} />
        </CardContent>
      </Card>
    </div>
  );
}
