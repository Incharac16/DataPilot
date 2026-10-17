import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";

export function AppLayout() {
  return (
    <div className="flex min-h-screen w-full min-w-0 bg-background">
      <Sidebar />
      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <Navbar />
        <main className="w-full min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full min-w-0 max-w-screen-2xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
