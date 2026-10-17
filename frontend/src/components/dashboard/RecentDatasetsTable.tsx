import { Link } from "react-router-dom";
import { FileSpreadsheet } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/common/EmptyState";
import { formatBytes, formatDate } from "@/lib/utils";
import { paths } from "@/routes/paths";
import type { UploadResponse } from "@/types/api";
import { Trash2 } from "lucide-react";

export function RecentDatasetsTable({
  datasets,
  onDelete,
  deletingId,
  openAnalytics = false,
}: {
  datasets: UploadResponse[];
  onDelete?: (id: string) => void;
  deletingId?: string;
  openAnalytics?: boolean;
}) {
  if (datasets.length === 0) {
    return (
      <EmptyState
        icon={FileSpreadsheet}
        title="No datasets yet"
        description="Upload a CSV or XLSX file to see it show up here."
      />
    );
  }

  return (
    <div className="max-w-full overflow-x-auto rounded-xl border border-border">
      <table className="w-full min-w-[640px] table-fixed text-sm">
        <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="w-[40%] px-4 py-3 font-medium">Name</th>
            <th className="px-4 py-3 font-medium">Rows</th>
            <th className="px-4 py-3 font-medium">Columns</th>
            <th className="px-4 py-3 font-medium">Size</th>
            <th className="px-4 py-3 font-medium">Uploaded</th>
            {onDelete && <th className="w-20 px-4 py-3 font-medium">Actions</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {datasets.map((d) => (
            <tr key={d.id} className="transition-colors hover:bg-muted/40">
              <td className="max-w-0 px-4 py-3">
                <Link to={openAnalytics ? paths.analytics(d.id) : paths.datasetPreview(d.id)} className="flex min-w-0 items-center gap-2 font-medium text-foreground hover:text-primary">
                  <FileSpreadsheet className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="truncate" title={d.filename}>{d.filename}</span>
                </Link>
                {d.status === "missing" && <span className="ml-6 text-xs text-destructive">Stored file missing</span>}
              </td>
              <td className="px-4 py-3 text-muted-foreground">{d.rows.toLocaleString()}</td>
              <td className="px-4 py-3 text-muted-foreground">{d.columns}</td>
              <td className="px-4 py-3 text-muted-foreground">{formatBytes(d.size_bytes)}</td>
              <td className="px-4 py-3">
                <Badge variant="secondary">{formatDate(d.uploaded_at)}</Badge>
              </td>
              {onDelete && (
                <td className="px-4 py-3">
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Delete ${d.filename}`}
                    disabled={deletingId === d.id}
                    onClick={() => onDelete(d.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
