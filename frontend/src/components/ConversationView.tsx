import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
  thinking: boolean;
}

export function ConversationView({ messages, thinking }: Props) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, thinking]);

  if (messages.length === 0 && !thinking) {
    return (
      <div className="flex flex-1 items-center justify-center px-6 text-center text-sm text-slate-500">
        <div>
          <p className="text-base text-slate-300">Good to see you.</p>
          <p className="mt-2 max-w-md">
            Try: <span className="text-accent-300">“open Chrome”</span>,{" "}
            <span className="text-accent-300">“summarize ~/notes/today.md”</span>,{" "}
            <span className="text-accent-300">“remind me to ship the PR”</span>, or{" "}
            <span className="text-accent-300">“what's on Hacker News right now?”</span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-6 py-4">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      {thinking && (
        <div className="flex justify-start">
          <div className="rounded-2xl border border-ink-700 bg-ink-800/80 px-4 py-3 text-sm text-slate-400">
            <span className="inline-flex items-center gap-1">
              <Dot delay={0} />
              <Dot delay={150} />
              <Dot delay={300} />
            </span>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

function Dot({ delay }: { delay: number }) {
  return (
    <span
      className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-400"
      style={{ animationDelay: `${delay}ms` }}
    />
  );
}
