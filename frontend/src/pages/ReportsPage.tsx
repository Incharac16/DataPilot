import { useParams } from "react-router-dom";
import { useState } from "react";
import { Download, FileText, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/common/EmptyState";
import { MarkdownMessage } from "@/components/chat/MarkdownMessage";
import { useDatasetInsights, useDatasetSummary } from "@/hooks/useDataset";
import { useToast } from "@/hooks/use-toast";
import { ApiError } from "@/services/api";

export default function ReportsPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const { data: summary } = useDatasetSummary(datasetId);
  const insights = useDatasetInsights(datasetId);
  const { toast } = useToast();
  const [report, setReport] = useState<string | null>(null);
  const [verifiedFacts, setVerifiedFacts] = useState<string[]>([]);

  const handleGenerate = async () => {
    try {
      const result = await insights.mutateAsync({
        question: "Generate a full written report summarizing key trends, outliers, and data quality issues in this dataset.",
      });
      setReport(result.insights);
      setVerifiedFacts(result.verified_facts);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Couldn't generate a report right now.";
      toast({ variant: "destructive", title: "Report generation failed", description: message });
    }
  };

  const handleExport = () => {
    if (!report) return;
    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${summary?.filename ?? "report"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Generated report"
        description="An AI-written summary of this dataset's trends and quality."
        actions={
          <>
            <Button variant="outline" onClick={handleExport} disabled={!report}>
              <Download className="h-4 w-4" />
              Export .md
            </Button>
            <Button onClick={handleGenerate} disabled={insights.isPending}>
              <Sparkles className="h-4 w-4" />
              {report ? "Regenerate" : "Generate report"}
            </Button>
          </>
        }
      />

      <Card>
        <CardContent className="p-6">
          {!report && !insights.isPending && (
            <EmptyState icon={FileText} title="No report yet" description='Click "Generate report" to have the AI summarize this dataset.' />
          )}
          {insights.isPending && <p className="text-sm text-muted-foreground">Generating report…</p>}
          {report && !insights.isPending && <MarkdownMessage content={report} />}
          {report && !insights.isPending && verifiedFacts.length > 0 && (
            <div className="mt-6 rounded-lg border border-border bg-muted/30 p-4">
              <h2 className="mb-2 text-sm font-semibold">Verified dataset facts</h2>
              <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                {verifiedFacts.map((fact) => <li key={fact}>{fact}</li>)}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <p className="mt-3 text-xs text-muted-foreground">
        Download this AI-written narrative as Markdown. A deterministic dataset PDF report is available from the dataset Analytics page.
      </p>
    </div>
  );
}
