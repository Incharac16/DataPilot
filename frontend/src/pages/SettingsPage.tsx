import { useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "@/context/ThemeContext";
import { useSettings } from "@/context/SettingsContext";
import { useToast } from "@/hooks/use-toast";

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  const { backendUrl, setBackendUrl } = useSettings();
  const [draftUrl, setDraftUrl] = useState(backendUrl);
  const { toast } = useToast();

  const handleSave = () => {
    setBackendUrl(draftUrl);
    toast({ title: "Settings saved", description: "Reload the app for the backend URL change to fully apply." });
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="Settings" description="Manage your preferences and backend connection." />

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Choose how DataPilot looks on this device.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <Label htmlFor="dark-mode">Dark mode</Label>
          <Switch id="dark-mode" checked={theme === "dark"} onCheckedChange={toggleTheme} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Backend connection</CardTitle>
          <CardDescription>
            The FastAPI backend base URL. Defaults to <code className="rounded bg-muted px-1">VITE_BACKEND_URL</code> from your environment.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="backend-url">Backend URL</Label>
            <Input
              id="backend-url"
              placeholder="http://localhost:8000"
              value={draftUrl}
              onChange={(e) => setDraftUrl(e.target.value)}
            />
          </div>
          <Button onClick={handleSave}>Save</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>About</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>DataPilot — AI-powered dataset analysis. Frontend: React 19, TypeScript, Vite, Tailwind CSS.</p>
          <p className="mt-1">Backend: FastAPI, Pandas, Plotly.</p>
        </CardContent>
      </Card>
    </div>
  );
}
