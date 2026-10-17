import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  History,
  Settings,
  Gauge,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { paths } from "@/routes/paths";
import { useState } from "react";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: paths.dashboard, label: "Dashboard", icon: LayoutDashboard },
  { to: paths.upload, label: "Upload Dataset", icon: Upload },
  { to: paths.history, label: "History", icon: History },
  { to: paths.settings, label: "Settings", icon: Settings },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-card/40 transition-all duration-200 md:flex",
        collapsed ? "w-[76px]" : "w-64"
      )}
    >
      <div className="flex h-16 items-center gap-2 px-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Gauge className="h-5 w-5" />
        </div>
        {!collapsed && <span className="text-lg font-semibold tracking-tight">DataPilot</span>}
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )
            }
          >
            <item.icon className="h-4.5 w-4.5 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-center"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        </Button>
      </div>
    </aside>
  );
}
