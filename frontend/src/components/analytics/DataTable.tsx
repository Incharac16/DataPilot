import { ArrowUpDown, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/common/EmptyState";

interface DataTableProps {
  rows: Record<string, unknown>[];
  columns: string[];
  search: string;
  onSearchChange: (value: string) => void;
  currentPage: number;
  pageSize: number;
  matchingRows: number;
  totalRows: number;
  onPageChange: (page: number) => void;
  sortBy?: string;
  sortDesc: boolean;
  onSortChange: (column: string, descending: boolean) => void;
}

export function DataTable({
  rows,
  columns,
  search,
  onSearchChange,
  currentPage,
  pageSize,
  matchingRows,
  totalRows,
  onPageChange,
  sortBy,
  sortDesc,
  onSortChange,
}: DataTableProps) {
  const totalPages = Math.max(1, Math.ceil(matchingRows / pageSize));

  const toggleSort = (col: string) => {
    onSortChange(col, sortBy === col ? !sortDesc : false);
  };

  if (totalRows === 0) {
    return <EmptyState icon={Search} title="No rows to display" description="This dataset preview is empty." />;
  }

  return (
    <div className="min-w-0">
      <div className="relative mb-4 max-w-xs">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search rows…"
          className="pl-9"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      <div className="max-h-[28rem] max-w-full overflow-auto rounded-xl border border-border">
        <table className="w-max min-w-full table-fixed text-sm">
          <colgroup>
            {columns.map((col) => <col key={col} className="w-56" />)}
          </colgroup>
          <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  aria-sort={sortBy === col ? (sortDesc ? "descending" : "ascending") : "none"}
                  className="sticky top-0 z-10 max-w-56 truncate bg-muted px-4 py-3 font-medium"
                >
                  <button
                    className="flex max-w-full items-center gap-1 hover:text-foreground"
                    title={col}
                    onClick={() => toggleSort(col)}
                  >
                    <span className="truncate">{col}</span>
                    <ArrowUpDown className="h-3 w-3 shrink-0" aria-hidden="true" />
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-muted/40">
                {columns.map((col) => (
                  <td
                    key={col}
                    className="max-w-56 truncate px-4 py-2.5 text-muted-foreground"
                    title={String(row[col] ?? "—")}
                  >
                    {String(row[col] ?? "—")}
                  </td>
                ))}
              </tr>
            ))}
            {matchingRows === 0 && (
              <tr>
                <td colSpan={Math.max(columns.length, 1)} className="px-4 py-8 text-center text-muted-foreground">
                  No matching rows.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {matchingRows === 0
            ? `0 matching rows · ${totalRows.toLocaleString()} total`
            : `Page ${currentPage} of ${totalPages} · ${matchingRows.toLocaleString()} matching rows · ${totalRows.toLocaleString()} total`}
        </span>
        {totalPages > 1 && (
          <div className="flex gap-2">
            <button
              className="rounded-md border border-border px-3 py-1.5 disabled:opacity-40"
              disabled={currentPage === 1}
              onClick={() => onPageChange(Math.max(1, currentPage - 1))}
            >
              Previous
            </button>
            <button
              className="rounded-md border border-border px-3 py-1.5 disabled:opacity-40"
              disabled={currentPage === totalPages}
              onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
