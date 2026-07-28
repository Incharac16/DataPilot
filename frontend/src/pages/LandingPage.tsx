import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, MessageSquare, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { paths } from "@/routes/paths";

const features = [
  { icon: UploadCloud, title: "Upload in seconds", description: "Drop in a CSV or XLSX file and get a structured summary instantly." },
  { icon: BarChart3, title: "Automatic charts", description: "Plotly-powered visualizations generated straight from your data's shape." },
  { icon: MessageSquare, title: "Ask your data questions", description: "Get plain-English answers about trends, outliers, and data quality." },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2 text-lg font-semibold tracking-tight">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">D</div>
          DataPilot
        </div>
        <Button asChild>
          <Link to={paths.dashboard}>
            Open app <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-24 text-center">
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Turn raw spreadsheets into <span className="text-gradient">answers</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
          Upload a dataset, get instant summaries, charts, and AI-generated insights — no formulas required.
        </p>
        <Button asChild size="lg" className="mt-8">
          <Link to={paths.upload}>
            Upload your first dataset <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </section>

      <section className="mx-auto grid max-w-5xl grid-cols-1 gap-6 px-6 pb-24 sm:grid-cols-3">
        {features.map((f) => (
          <div key={f.title} className="rounded-xl border border-border bg-card p-6">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <f.icon className="h-5 w-5 text-primary" />
            </div>
            <h3 className="font-semibold">{f.title}</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">{f.description}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
