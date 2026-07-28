import { useCallback, useRef, useState } from "react";
import { FileSpreadsheet, UploadCloud } from "lucide-react";
import { cn, formatBytes } from "@/lib/utils";

const ACCEPTED_TYPES = [".csv", ".xlsx", ".xls"];
const MAX_SIZE_BYTES = 50 * 1024 * 1024; // 50MB default, mirrors backend MAX_UPLOAD_MB

interface DropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function Dropzone({ onFileSelected, disabled }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndEmit = useCallback(
    (file: File) => {
      const ext = `.${file.name.split(".").pop()?.toLowerCase()}`;
      if (!ACCEPTED_TYPES.includes(ext)) {
        setError(`Unsupported file type "${ext}". Upload a CSV or XLSX file.`);
        return;
      }
      if (file.size > MAX_SIZE_BYTES) {
        setError(`File is ${formatBytes(file.size)}, which exceeds the ${formatBytes(MAX_SIZE_BYTES)} limit.`);
        return;
      }
      setError(null);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndEmit(file);
  };

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-16 text-center transition-colors",
          isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/40",
          disabled && "pointer-events-none opacity-60"
        )}
      >
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          {isDragging ? (
            <FileSpreadsheet className="h-7 w-7 text-primary" />
          ) : (
            <UploadCloud className="h-7 w-7 text-primary" />
          )}
        </div>
        <p className="text-sm font-medium">
          <span className="text-primary">Click to upload</span> or drag and drop
        </p>
        <p className="mt-1 text-xs text-muted-foreground">CSV or XLSX, up to {formatBytes(MAX_SIZE_BYTES)}</p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_TYPES.join(",")}
          className="hidden"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) validateAndEmit(file);
            e.target.value = "";
          }}
        />
      </div>
      {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
    </div>
  );
}
