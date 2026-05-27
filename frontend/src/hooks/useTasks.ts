import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { TaskItem } from "@/lib/types";

export function useTasks() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await api.listTasks();
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    refresh();
    const handle = window.setInterval(refresh, 8_000);
    return () => window.clearInterval(handle);
  }, [refresh]);

  const create = useCallback(
    async (title: string) => {
      const trimmed = title.trim();
      if (!trimmed) return;
      await api.createTask({ title: trimmed });
      await refresh();
    },
    [refresh],
  );

  const complete = useCallback(
    async (id: number) => {
      await api.completeTask(id);
      await refresh();
    },
    [refresh],
  );

  const remove = useCallback(
    async (id: number) => {
      await api.deleteTask(id);
      await refresh();
    },
    [refresh],
  );

  return { tasks, error, refresh, create, complete, remove };
}
