import { Fragment } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ColumnSummary } from "@/types/api";
import { formatNumber } from "@/lib/utils";

export function ColumnSummaryCard({ column }: { column: ColumnSummary }) {
  const stats: [string, string][] = [];
  if (column.mean !== undefined) stats.push(["Mean", formatNumber(column.mean)]);
  if (column.median !== undefined) stats.push(["Median", formatNumber(column.median)]);
  if (column.std !== undefined) stats.push(["Std dev", formatNumber(column.std)]);
  if (column.min !== undefined) stats.push(["Min", formatNumber(column.min)]);
  if (column.max !== undefined) stats.push(["Max", formatNumber(column.max)]);
  if (column.top_value !== undefined) stats.push(["Most common", column.top_value]);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <p className="truncate text-sm font-semibold" title={column.name}>
            {column.name}
          </p>
          <Badge variant="outline">{column.dtype}</Badge>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
          <span className="text-muted-foreground">Missing</span>
          <span className="text-right font-medium">
            {column.missing_count.toLocaleString()} ({column.missing_pct.toFixed(1)}%)
          </span>
          <span className="text-muted-foreground">Unique</span>
          <span className="text-right font-medium">{column.unique_count.toLocaleString()}</span>
          {stats.map(([label, value]) => (
            <Fragment key={label}>
              <span className="text-muted-foreground">{label}</span>
              <span className="text-right font-medium">{value}</span>
            </Fragment>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
