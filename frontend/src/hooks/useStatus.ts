import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SystemStatus } from "@/lib/types";

const REFRESH_MS = 5_000;

export function useStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function refresh() {
      try {
        const data = await api.status();
        if (active) {
          setStatus(data);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    }

    refresh();
    const handle = window.setInterval(refresh, REFRESH_MS);
    return () => {
      active = false;
      window.clearInterval(handle);
    };
  }, []);

  return { status, error };
}
