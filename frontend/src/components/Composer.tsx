import { useCallback, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { MicButton } from "./MicButton";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function Composer({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const submit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
  }, [value, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submit();
      }
    },
    [submit],
  );

  return (
    <div className="card flex gap-4 p-4">
      <MicButton
        disabled={disabled}
        onTranscript={(text) => {
          setValue((prev) => (prev ? `${prev} ${text}` : text));
          textareaRef.current?.focus();
        }}
      />
      <div className="flex flex-1 flex-col gap-3">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          placeholder="Ask Jarvis to open an app, browse a URL, summarize a file, manage tasks…"
          className="min-h-[64px] w-full resize-none rounded-xl border border-ink-700 bg-ink-800/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-accent-500 focus:outline-none"
          disabled={disabled}
        />
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>
            <kbd className="rounded border border-ink-600 bg-ink-800 px-1.5 py-0.5 font-mono text-[10px]">
              Enter
            </kbd>{" "}
            to send,{" "}
            <kbd className="rounded border border-ink-600 bg-ink-800 px-1.5 py-0.5 font-mono text-[10px]">
              Shift + Enter
            </kbd>{" "}
            for newline
          </span>
          <button
            type="button"
            onClick={submit}
            disabled={disabled || !value.trim()}
            className={clsx(
              "rounded-lg border border-accent-500/50 bg-accent-500/10 px-4 py-2 text-sm font-medium text-accent-300 transition",
              "hover:border-accent-500 hover:bg-accent-500/20 hover:text-accent-200",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
