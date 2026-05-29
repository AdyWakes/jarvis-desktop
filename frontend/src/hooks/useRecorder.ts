import { useCallback, useEffect, useRef, useState } from "react";

type RecorderState = "idle" | "requesting" | "recording" | "processing" | "error";

const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/mp4",
];

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  for (const mime of PREFERRED_MIME_TYPES) {
    if (MediaRecorder.isTypeSupported(mime)) return mime;
  }
  return undefined;
}

export function useRecorder() {
  const [state, setState] = useState<RecorderState>("idle");
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const resolveRef = useRef<((blob: Blob) => void) | null>(null);
  const rejectRef = useRef<((reason: unknown) => void) | null>(null);

  const cleanupStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => () => cleanupStream(), [cleanupStream]);

  const start = useCallback(async () => {
    if (state === "recording" || state === "requesting") return;
    setError(null);
    setState("requesting");
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setState("error");
      setError("Microphone access is not available in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const type = recorder.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        cleanupStream();
        resolveRef.current?.(blob);
        resolveRef.current = null;
        rejectRef.current = null;
      };
      recorder.onerror = (e) => {
        rejectRef.current?.(e);
        resolveRef.current = null;
        rejectRef.current = null;
        setState("error");
      };
      recorderRef.current = recorder;
      recorder.start();
      setState("recording");
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Failed to start recording.");
      cleanupStream();
    }
  }, [cleanupStream, state]);

  const stop = useCallback(async (): Promise<Blob | null> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      return null;
    }
    setState("processing");
    return new Promise<Blob>((resolve, reject) => {
      resolveRef.current = resolve;
      rejectRef.current = reject;
      recorder.stop();
    })
      .then((blob) => {
        recorderRef.current = null;
        setState("idle");
        return blob;
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Recorder error.");
        setState("error");
        return null;
      });
  }, []);

  const cancel = useCallback(() => {
    recorderRef.current?.stop();
    recorderRef.current = null;
    cleanupStream();
    setState("idle");
  }, [cleanupStream]);

  return { state, error, start, stop, cancel };
}
