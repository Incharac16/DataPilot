import { Fragment } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ColumnSummary } from "@/types/api";
import { formatNumber } from "@/lib/utils";

const TYPE_LABELS: Record<ColumnSummary["semantic_type"], string> = {
  numeric: "Numeric",
  categorical: "Categorical",
  boolean: "Boolean",
  datetime: "Datetime",
  identifier: "Identifier",
  unknown: "Unknown",
};

export function ColumnSummaryCard({ column }: { column: ColumnSummary }) {
  const stats: [string, string][] = [];
  if (column.semantic_type === "numeric") {
    if (column.mean !== null) stats.push(["Mean", formatNumber(column.mean)]);
    if (column.median !== null) stats.push(["Median", formatNumber(column.median)]);
    if (column.std !== null) stats.push(["Std dev", formatNumber(column.std)]);
    if (column.min !== null) stats.push(["Min", formatNumber(column.min)]);
    if (column.max !== null) stats.push(["Max", formatNumber(column.max)]);
  }
  if (column.semantic_type === "boolean") {
    if (column.true_count !== null && column.true_pct !== null) {
      stats.push(["True", `${column.true_count.toLocaleString()} (${column.true_pct.toFixed(1)}%)`]);
    }
    if (column.false_count !== null && column.false_pct !== null) {
      stats.push(["False", `${column.false_count.toLocaleString()} (${column.false_pct.toFixed(1)}%)`]);
    }
  }
  if (column.semantic_type === "datetime") {
    if (column.earliest) stats.push(["Earliest", column.earliest]);
    if (column.latest) stats.push(["Latest", column.latest]);
  }

  stats.push([
    column.top_value_status === "repeated" || column.top_value_status === "tie"
      ? "Most common"
      : "Value frequency",
    column.top_value_count === null || column.top_value_status === "tie"
      ? column.top_value ?? "No available values"
      : `${column.top_value} (${column.top_value_count.toLocaleString()} occurrences)`,
  ]);
  if (column.semantic_type === "identifier") {
    stats.push(["Repeated values", column.duplicate_value_count.toLocaleString()]);
  }
  if (column.format_issue_count > 0) {
    stats.push(["Format issues", column.format_issue_count.toLocaleString()]);
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <p className="min-w-0 break-all text-sm font-semibold" title={column.name}>
            {column.name}
          </p>
          <Badge variant="outline" title={column.identifier_reason ?? column.dtype}>
            {TYPE_LABELS[column.semantic_type]}
          </Badge>
        </div>
        {column.identifier_reason && (
          <p className="mt-1 break-words text-xs text-muted-foreground" title={column.identifier_reason}>
            {column.identifier_reason}
          </p>
        )}
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
              <span className="break-words text-right font-medium" title={value}>{value}</span>
            </Fragment>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
