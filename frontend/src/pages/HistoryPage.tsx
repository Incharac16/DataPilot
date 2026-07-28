import { History as HistoryIcon, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { RecentDatasetsTable } from "@/components/dashboard/RecentDatasetsTable";
import { Button } from "@/components/ui/button";
import { useLocalDatasets } from "@/hooks/useLocalDatasets";
import { useToast } from "@/hooks/use-toast";

export default function HistoryPage() {
  const { datasets, clearDatasets } = useLocalDatasets();
  const { toast } = useToast();

  return (
    <div>
      <PageHeader
        title="History"
        description="Datasets you've uploaded in this browser."
        actions={
          datasets.length > 0 && (
            <Button
              variant="outline"
              onClick={() => {
                clearDatasets();
                toast({ title: "History cleared" });
              }}
            >
              <Trash2 className="h-4 w-4" />
              Clear history
            </Button>
          )
        }
      />
      <RecentDatasetsTable datasets={datasets} />
      {datasets.length === 0 && (
        <p className="mt-4 flex items-center gap-1.5 text-xs text-muted-foreground">
          <HistoryIcon className="h-3.5 w-3.5" />
          History is tracked locally in this browser — the backend doesn't expose a dataset-listing endpoint yet.
        </p>
      )}
    </div>
  );
}
