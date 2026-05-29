import { useCallback, useState } from "react";
import clsx from "clsx";
import { useRecorder } from "@/hooks/useRecorder";
import { api } from "@/lib/api";

interface Props {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export function MicButton({ onTranscript, disabled }: Props) {
  const recorder = useRecorder();
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isRecording = recorder.state === "recording";
  const busy = transcribing || recorder.state === "requesting" || recorder.state === "processing";

  const handleClick = useCallback(async () => {
    setError(null);
    if (isRecording) {
      const blob = await recorder.stop();
      if (!blob) return;
      setTranscribing(true);
      try {
        const ext = blob.type.includes("mp4")
          ? "mp4"
          : blob.type.includes("ogg")
            ? "ogg"
            : "webm";
        const { text } = await api.transcribe(blob, `clip.${ext}`);
        if (text.trim()) {
          onTranscript(text.trim());
        } else {
          setError("No speech detected.");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Transcription failed.");
      } finally {
        setTranscribing(false);
      }
    } else {
      await recorder.start();
    }
  }, [isRecording, onTranscript, recorder]);

  const label = transcribing
    ? "Transcribing…"
    : isRecording
      ? "Stop"
      : recorder.state === "requesting"
        ? "Listening…"
        : "Hold to speak";

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || busy}
        className={clsx(
          "relative flex h-20 w-20 items-center justify-center rounded-full border transition focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500",
          isRecording
            ? "border-red-500/60 bg-red-500/10 text-red-300 shadow-glow"
            : "border-accent-500/50 bg-ink-800/80 text-accent-400 hover:border-accent-500 hover:text-accent-300",
          (disabled || busy) && "cursor-not-allowed opacity-60",
        )}
        aria-pressed={isRecording}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
      >
        {isRecording && (
          <span className="pointer-events-none absolute inset-0 animate-ping rounded-full border border-red-500/40" />
        )}
        <MicIcon className="h-8 w-8" />
      </button>
      <span className="text-xs text-slate-400">{label}</span>
      {(error || recorder.error) && (
        <span className="text-xs text-red-400">{error ?? recorder.error}</span>
      )}
    </div>
  );
}

function MicIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <path d="M12 18v3" />
      <path d="M8 21h8" />
    </svg>
  );
}
