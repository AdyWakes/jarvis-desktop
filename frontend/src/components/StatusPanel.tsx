import clsx from "clsx";
import type { SystemStatus } from "@/lib/types";

interface Props {
  status: SystemStatus | null;
  error: string | null;
  socketStatus: string;
}

function formatUptime(seconds: number): string {
  if (!Number.isFinite(seconds)) return "—";
  const s = Math.floor(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

export function StatusPanel({ status, error, socketStatus }: Props) {
  return (
    <aside className="card flex h-full flex-col gap-4 p-5">
      <header className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          System
        </h2>
        <span
          className={clsx(
            "pill",
            socketStatus === "open"
              ? "pill-positive"
              : socketStatus === "connecting"
                ? "pill-warn"
                : "pill-error",
          )}
        >
          <Dot status={socketStatus} /> {socketStatus}
        </span>
      </header>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          {error}
        </div>
      )}

      <dl className="grid grid-cols-2 gap-3 text-xs">
        <Metric label="Version" value={status?.version ?? "—"} />
        <Metric label="Uptime" value={formatUptime(status?.uptime_seconds ?? 0)} />
        <Metric
          label="CPU"
          value={status ? `${status.cpu_percent.toFixed(1)}%` : "—"}
          accent={status ? barAccent(status.cpu_percent) : undefined}
        />
        <Metric
          label="Memory"
          value={status ? `${status.memory_percent.toFixed(1)}%` : "—"}
          accent={status ? barAccent(status.memory_percent) : undefined}
        />
      </dl>

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          OpenAI
        </h3>
        <span
          className={clsx(
            "pill",
            status?.openai_configured ? "pill-positive" : "pill-error",
          )}
        >
          {status?.openai_configured ? "configured" : "missing API key"}
        </span>
      </div>

      <div className="flex-1 overflow-hidden">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Tools ({status?.tools.length ?? 0})
        </h3>
        <ul className="space-y-2 overflow-y-auto pr-1 text-xs">
          {(status?.tools ?? []).map((tool) => (
            <li key={tool.name} className="rounded-lg border border-ink-700 bg-ink-800/60 p-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-accent-300">{tool.name}</span>
                <span className="pill">{tool.source}</span>
              </div>
              <p className="mt-1 text-slate-400">{tool.description}</p>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

function Metric({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-ink-700 bg-ink-800/60 p-3">
      <dt className="text-[10px] uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className={clsx("mt-1 text-sm font-semibold text-slate-100", accent)}>{value}</dd>
    </div>
  );
}

function barAccent(percent: number): string {
  if (percent >= 90) return "text-red-300";
  if (percent >= 75) return "text-amber-300";
  return "text-emerald-300";
}

function Dot({ status }: { status: string }) {
  return (
    <span
      className={clsx(
        "inline-block h-1.5 w-1.5 rounded-full",
        status === "open"
          ? "bg-emerald-400"
          : status === "connecting"
            ? "bg-amber-400 animate-pulse"
            : "bg-red-400",
      )}
    />
  );
}
