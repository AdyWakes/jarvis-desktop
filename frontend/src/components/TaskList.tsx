import { useState } from "react";
import clsx from "clsx";
import { useTasks } from "@/hooks/useTasks";

export function TaskList() {
  const { tasks, error, create, complete, remove } = useTasks();
  const [draft, setDraft] = useState("");

  const open = tasks.filter((t) => t.status === "open");
  const done = tasks.filter((t) => t.status === "done");

  return (
    <section className="card flex h-full flex-col gap-3 p-5">
      <header className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          Tasks
        </h2>
        <span className="pill">{open.length} open</span>
      </header>

      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!draft.trim()) return;
          await create(draft);
          setDraft("");
        }}
        className="flex gap-2"
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="New task…"
          className="flex-1 rounded-lg border border-ink-700 bg-ink-800/70 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-accent-500 focus:outline-none"
        />
        <button
          type="submit"
          className="rounded-lg border border-ink-700 bg-ink-800/80 px-3 py-2 text-sm text-slate-200 transition hover:border-accent-500 hover:text-accent-300"
        >
          Add
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          {error}
        </div>
      )}

      <ul className="space-y-2 overflow-y-auto pr-1 text-sm">
        {open.length === 0 && done.length === 0 && (
          <li className="rounded-lg border border-dashed border-ink-700 px-3 py-4 text-center text-xs text-slate-500">
            No tasks yet. Ask Jarvis to add one, or use the field above.
          </li>
        )}
        {open.map((task) => (
          <li
            key={task.id}
            className="flex items-start gap-2 rounded-lg border border-ink-700 bg-ink-800/60 px-3 py-2"
          >
            <button
              type="button"
              onClick={() => complete(task.id)}
              className="mt-0.5 h-4 w-4 flex-shrink-0 rounded border border-ink-600 transition hover:border-accent-500 hover:bg-accent-500/10"
              aria-label="Mark complete"
            />
            <div className="flex-1">
              <div className="text-slate-100">{task.title}</div>
              {task.notes && <div className="text-xs text-slate-400">{task.notes}</div>}
            </div>
            <button
              type="button"
              onClick={() => remove(task.id)}
              className="text-xs text-slate-500 transition hover:text-red-300"
              aria-label="Delete task"
            >
              ✕
            </button>
          </li>
        ))}
        {done.slice(0, 4).map((task) => (
          <li
            key={task.id}
            className={clsx(
              "flex items-start gap-2 rounded-lg border border-ink-700 bg-ink-800/30 px-3 py-2 text-slate-500",
            )}
          >
            <span className="mt-0.5 h-4 w-4 flex-shrink-0 rounded border border-emerald-500/40 bg-emerald-500/10" />
            <div className="flex-1 line-through">{task.title}</div>
            <button
              type="button"
              onClick={() => remove(task.id)}
              className="text-xs text-slate-500 transition hover:text-red-300"
              aria-label="Delete task"
            >
              ✕
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
