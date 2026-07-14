import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

const STORAGE_KEY = "imr_admin_api_key";
const DEMO_KEY = "imr_demo_key_change_me_in_production_abc123";

type AuthContextValue = {
  apiKey: string;
  setApiKey: (key: string) => void;
  clearApiKey: () => void;
  demoKey: string;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKeyState] = useState(
    () => localStorage.getItem(STORAGE_KEY) ?? DEMO_KEY,
  );

  const value = useMemo(
    () => ({
      apiKey,
      demoKey: DEMO_KEY,
      setApiKey: (key: string) => {
        const next = key.trim();
        setApiKeyState(next);
        localStorage.setItem(STORAGE_KEY, next);
      },
      clearApiKey: () => {
        setApiKeyState("");
        localStorage.removeItem(STORAGE_KEY);
      },
    }),
    [apiKey],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
