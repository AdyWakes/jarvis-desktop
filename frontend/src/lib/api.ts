import type { SystemStatus, TaskItem, TranscriptionResponse } from "./types";

const RAW_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const BASE = RAW_BASE.replace(/\/$/, "");

function url(path: string): string {
  if (BASE) return `${BASE}${path}`;
  // Same-origin: rely on the Vite dev-proxy '/api/*' rewrite to backend root.
  return `/api${path}`;
}

function wsUrl(path: string): string {
  const httpUrl = url(path);
  if (httpUrl.startsWith("http")) {
    return httpUrl.replace(/^http/, "ws");
  }
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}${httpUrl}`;
}

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail || "request failed"}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  status: () => jsonFetch<SystemStatus>("/status"),

  listTasks: (statusFilter?: "open" | "done") => {
    const qs = statusFilter ? `?status_filter=${statusFilter}` : "";
    return jsonFetch<TaskItem[]>(`/tasks${qs}`);
  },

  createTask: (payload: { title: string; notes?: string }) =>
    jsonFetch<TaskItem>("/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  completeTask: (id: number) =>
    jsonFetch<TaskItem>(`/tasks/${id}/complete`, { method: "POST" }),

  deleteTask: (id: number) =>
    jsonFetch<void>(`/tasks/${id}`, { method: "DELETE" }),

  transcribe: async (blob: Blob, filename = "audio.webm"): Promise<TranscriptionResponse> => {
    const form = new FormData();
    form.append("audio", blob, filename);
    const res = await fetch(url("/stt"), { method: "POST", body: form });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${detail || "transcription failed"}`);
    }
    return (await res.json()) as TranscriptionResponse;
  },

  chatSocket: () => new WebSocket(wsUrl("/chat/ws")),
};
