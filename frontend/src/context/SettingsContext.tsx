import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

interface SettingsContextValue {
  backendUrl: string;
  setBackendUrl: (url: string) => void;
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);
const STORAGE_KEY = "datapilot-backend-url";

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [backendUrl, setBackendUrlState] = useState<string>(
    () => window.localStorage.getItem(STORAGE_KEY) || import.meta.env.VITE_BACKEND_URL || ""
  );

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, backendUrl);
  }, [backendUrl]);

  return (
    <SettingsContext.Provider value={{ backendUrl, setBackendUrl: setBackendUrlState }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within a SettingsProvider");
  return ctx;
}
