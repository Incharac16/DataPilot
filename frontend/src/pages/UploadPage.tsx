import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/common/PageHeader";
import { Dropzone } from "@/components/upload/Dropzone";
import { UploadProgress } from "@/components/upload/UploadProgress";
import { Card, CardContent } from "@/components/ui/card";
import { useUploadConfig, useUploadDataset } from "@/hooks/useDataset";
import { useLocalDatasets } from "@/hooks/useLocalDatasets";
import { useToast } from "@/hooks/use-toast";
import { paths } from "@/routes/paths";
import { ApiError } from "@/services/api";

export default function UploadPage() {
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  const navigate = useNavigate();
  const { toast } = useToast();
  const { addDataset } = useLocalDatasets();
  const uploadConfig = useUploadConfig();
  const upload = useUploadDataset();

  const handleFile = async (file: File) => {
    setPendingFile(file);

    try {
      const result = await upload.mutateAsync(file);

      addDataset(result);

      const datasetId = result.id;

      if (!datasetId) {
        throw new Error("Backend did not return a dataset ID.");
      }

      toast({
        title: "Upload complete",
        description: `${file.name} is ready to explore.`,
      });

      navigate(paths.datasetPreview(datasetId));
    } catch (err) {
      console.error(err);

      const message =
        err instanceof ApiError
          ? err.message
          : "Please check your connection and try again.";

      toast({
        variant: "destructive",
        title: "Upload failed",
        description: message,
      });

      setPendingFile(null);
    }
  };

  const status = upload.isPending
    ? upload.progress >= 100
      ? "processing"
      : "uploading"
    : upload.isError
      ? "error"
      : "done";

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        title="Upload dataset"
        description="Upload a CSV or XLSX file to start exploring."
      />

      <Card>
        <CardContent className="p-6">
          {!pendingFile || upload.isError ? (
            uploadConfig.isPending ? (
              <p className="text-sm text-muted-foreground">Loading upload settings…</p>
            ) : uploadConfig.isError ? (
              <p className="text-sm text-destructive">
                Could not load upload settings. Please refresh the page and try again.
              </p>
            ) : (
              <Dropzone
                onFileSelected={handleFile}
                maxUploadMb={uploadConfig.data.max_upload_mb}
                disabled={upload.isPending}
              />
            )
          ) : (
            <UploadProgress
              fileName={pendingFile.name}
              fileSize={pendingFile.size}
              progress={upload.progress}
              status={status}
              onCancel={() => setPendingFile(null)}
            />
          )}
        </CardContent>
      </Card>

      <ul className="mt-6 space-y-2 text-sm text-muted-foreground">
        <li>• Accepted formats: .csv, .xlsx, .xls</li>
        <li>• Your file is sent directly to your backend.</li>
        <li>• Large files may take a few extra seconds to process.</li>
      </ul>
    </div>
  );
}