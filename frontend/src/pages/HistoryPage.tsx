import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { History as HistoryIcon } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { RecentDatasetsTable } from "@/components/dashboard/RecentDatasetsTable";
import { deleteDataset, listDatasets } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import { ErrorState } from "@/components/common/ErrorState";
import { TableSkeleton } from "@/components/common/LoadingState";

export default function HistoryPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: datasets = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["datasets"],
    queryFn: listDatasets,
  });
  const removeDataset = useMutation({
    mutationFn: deleteDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      toast({ title: "Dataset deleted" });
    },
    onError: (error) => {
      toast({
        variant: "destructive",
        title: "Could not delete dataset",
        description: error instanceof Error ? error.message : "Please try again.",
      });
    },
  });

  return (
    <div>
      <PageHeader
        title="History"
        description="Datasets stored by this backend."
      />
      {isError ? (
        <ErrorState description="Couldn't load saved datasets." onRetry={() => refetch()} />
      ) : isLoading ? (
        <TableSkeleton />
      ) : (
        <RecentDatasetsTable
          datasets={datasets}
          onDelete={(id) => removeDataset.mutate(id)}
          deletingId={removeDataset.isPending ? removeDataset.variables : undefined}
          openAnalytics
        />
      )}
      {!isLoading && !isError && datasets.length === 0 && (
        <p className="mt-4 flex items-center gap-1.5 text-xs text-muted-foreground">
          <HistoryIcon className="h-3.5 w-3.5" />
          History is loaded from the backend's SQLite metadata store.
        </p>
      )}
    </div>
  );
}
