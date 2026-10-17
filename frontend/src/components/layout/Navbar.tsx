import { Link } from "react-router-dom";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Breadcrumb } from "@/components/layout/Breadcrumb";
import { paths } from "@/routes/paths";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 flex h-16 min-w-0 items-center justify-between gap-4 border-b border-border bg-background/80 px-4 backdrop-blur-xl sm:px-6">
      <div className="min-w-0 flex-1 overflow-hidden"><Breadcrumb /></div>
      <div className="flex items-center gap-2">
        <Button asChild size="sm">
          <Link to={paths.upload}>
            <Upload className="h-4 w-4" />
            Upload dataset
          </Link>
        </Button>
        <ThemeToggle />
      </div>
    </header>
  );
}
