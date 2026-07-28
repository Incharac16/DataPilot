import { Link } from "react-router-dom";
import { FileSpreadsheet } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/common/EmptyState";
import { formatBytes, formatDate } from "@/lib/utils";
import { paths } from "@/routes/paths";
import type { UploadResponse } from "@/types/api";

export function RecentDatasetsTable({ datasets }: { datasets: UploadResponse[] }) {
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
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">Name</th>
            <th className="px-4 py-3 font-medium">Rows</th>
            <th className="px-4 py-3 font-medium">Columns</th>
            <th className="px-4 py-3 font-medium">Size</th>
            <th className="px-4 py-3 font-medium">Uploaded</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {datasets.map((d) => (
            <tr key={d.id} className="transition-colors hover:bg-muted/40">
              <td className="px-4 py-3">
                <Link to={paths.datasetPreview(d.id)} className="flex items-center gap-2 font-medium text-foreground hover:text-primary">
                  <FileSpreadsheet className="h-4 w-4 shrink-0 text-muted-foreground" />
                  {d.filename}
                </Link>
              </td>
              <td className="px-4 py-3 text-muted-foreground">{d.rows.toLocaleString()}</td>
              <td className="px-4 py-3 text-muted-foreground">{d.columns}</td>
              <td className="px-4 py-3 text-muted-foreground">{formatBytes(d.size_bytes)}</td>
              <td className="px-4 py-3">
                <Badge variant="secondary">{formatDate(d.uploaded_at)}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
