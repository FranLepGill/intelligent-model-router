import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { useAuth } from "../auth";

export function useApiQuery<T>(loader: (apiKey: string) => Promise<T>) {
  const { apiKey } = useAuth();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    if (!apiKey) {
      setError("Configurá una API key para continuar.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await loader(apiKey);
      setData(result);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "No se pudo cargar la información.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [apiKey, loader]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, error, loading, reload };
}
