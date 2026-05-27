import { Composer } from "./components/Composer";
import { ConversationView } from "./components/ConversationView";
import { StatusPanel } from "./components/StatusPanel";
import { TaskList } from "./components/TaskList";
import { useChat } from "./hooks/useChat";
import { useStatus } from "./hooks/useStatus";

export default function App() {
  const chat = useChat();
  const status = useStatus();

  return (
    <div className="min-h-screen bg-gradient-to-br from-ink-950 via-ink-900 to-ink-950">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-4 px-4 py-6 lg:px-8">
        <Header socketStatus={chat.status} />

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
          <main className="card flex h-[78vh] min-h-[520px] flex-col overflow-hidden">
            <ConversationView messages={chat.messages} thinking={chat.thinking} />
            {chat.error && (
              <div className="border-t border-red-500/30 bg-red-500/10 px-6 py-2 text-xs text-red-300">
                {chat.error}
              </div>
            )}
            <div className="border-t border-ink-700 p-4">
              <Composer
                onSend={chat.send}
                disabled={chat.status !== "open" && chat.status !== "connecting"}
              />
            </div>
          </main>

          <aside className="grid grid-rows-2 gap-4">
            <StatusPanel
              status={status.status}
              error={status.error}
              socketStatus={chat.status}
            />
            <TaskList />
          </aside>
        </div>

        <Footer onReset={chat.reset} />
      </div>
    </div>
  );
}

function Header({ socketStatus }: { socketStatus: string }) {
  return (
    <header className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <LogoMark />
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-slate-100">
            Jarvis
          </h1>
          <p className="text-xs text-slate-400">Desktop assistant — voice, chat, tools</p>
        </div>
      </div>
      <div className="text-xs text-slate-500">
        Connection: <span className="text-slate-300">{socketStatus}</span>
      </div>
    </header>
  );
}

function Footer({ onReset }: { onReset: () => void }) {
  return (
    <footer className="flex items-center justify-between text-xs text-slate-500">
      <span>
        Backend at <code className="font-mono text-slate-300">{apiLabel()}</code>
      </span>
      <button
        type="button"
        onClick={onReset}
        className="rounded border border-ink-700 px-2 py-1 text-slate-400 transition hover:border-accent-500 hover:text-accent-300"
      >
        Reset conversation
      </button>
    </footer>
  );
}

function apiLabel(): string {
  const url = import.meta.env.VITE_API_BASE_URL ?? "";
  return url || "/api → http://localhost:8000";
}

function LogoMark() {
  return (
    <div className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-accent-500/40 bg-ink-800 shadow-glow">
      <div className="h-3 w-3 rounded-full bg-accent-500" />
      <div className="absolute inset-1 rounded-lg border border-accent-500/30" />
    </div>
  );
}
