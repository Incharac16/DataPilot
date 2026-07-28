import { FileSpreadsheet, X } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { formatBytes } from "@/lib/utils";

interface UploadProgressProps {
  fileName: string;
  fileSize: number;
  progress: number;
  status: "uploading" | "processing" | "done" | "error";
  onCancel?: () => void;
}

const statusLabel: Record<UploadProgressProps["status"], string> = {
  uploading: "Uploading…",
  processing: "Processing dataset…",
  done: "Ready",
  error: "Upload failed",
};

export function UploadProgress({ fileName, fileSize, progress, status, onCancel }: UploadProgressProps) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-border bg-card p-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
        <FileSpreadsheet className="h-5 w-5 text-primary" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate text-sm font-medium">{fileName}</p>
          <span className="shrink-0 text-xs text-muted-foreground">{formatBytes(fileSize)}</span>
        </div>
        <Progress value={status === "done" ? 100 : progress} className="mt-2" />
        <p className="mt-1 text-xs text-muted-foreground">{statusLabel[status]}</p>
      </div>
      {onCancel && status !== "done" && (
        <Button variant="ghost" size="icon" onClick={onCancel} aria-label="Cancel upload">
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
