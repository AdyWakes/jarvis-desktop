import clsx from "clsx";
import type { ChatMessage } from "@/lib/types";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div className={clsx("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[min(80ch,calc(100%-4rem))] rounded-2xl border px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "border-accent-500/30 bg-accent-500/10 text-accent-50"
            : "border-ink-700 bg-ink-800/80 text-slate-100",
        )}
      >
        <div className="mb-1 flex items-center justify-between gap-3 text-[10px] uppercase tracking-wider text-slate-400">
          <span>{isUser ? "You" : "Jarvis"}</span>
          <time>{new Date(message.createdAt).toLocaleTimeString()}</time>
        </div>
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
        {message.toolCalls && message.toolCalls.length > 0 && (
          <details className="mt-3 rounded-lg border border-ink-700 bg-ink-900/60 p-2 text-xs text-slate-400">
            <summary className="cursor-pointer select-none text-slate-300">
              {message.toolCalls.length} tool call
              {message.toolCalls.length === 1 ? "" : "s"}
            </summary>
            <ul className="mt-2 space-y-2">
              {message.toolCalls.map((call, idx) => (
                <li key={idx} className="rounded border border-ink-700 bg-ink-800/60 p-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-accent-300">{call.tool}</span>
                    {call.error ? (
                      <span className="pill pill-error">error</span>
                    ) : (
                      <span className="pill pill-positive">ok</span>
                    )}
                  </div>
                  <pre className="mt-1 overflow-x-auto whitespace-pre-wrap break-words text-[11px] text-slate-400">
                    {JSON.stringify(call.arguments, null, 2)}
                  </pre>
                  {call.error ? (
                    <div className="mt-1 text-[11px] text-red-300">{call.error}</div>
                  ) : (
                    <pre className="mt-1 max-h-40 overflow-y-auto whitespace-pre-wrap break-words text-[11px] text-slate-300">
                      {typeof call.result === "string"
                        ? call.result
                        : JSON.stringify(call.result, null, 2)}
                    </pre>
                  )}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
