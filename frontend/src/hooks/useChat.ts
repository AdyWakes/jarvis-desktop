import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ChatMessage, ToolCallRecord } from "@/lib/types";

type Status = "idle" | "connecting" | "open" | "closed" | "error";

interface ServerEvent {
  type: "tool_call" | "reply" | "error";
  tool?: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
  error?: string | null;
  conversation_id?: string;
  reply?: string;
}

function uid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const conversationIdRef = useRef<string | null>(null);
  const pendingToolCallsRef = useRef<ToolCallRecord[]>([]);

  const connect = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      return;
    }
    setStatus("connecting");
    setError(null);
    const ws = api.chatSocket();
    socketRef.current = ws;
    ws.onopen = () => {
      setStatus("open");
      setError(null);
    };
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => {
      setStatus("error");
      setError("WebSocket connection error");
    };
    ws.onmessage = (event) => {
      let payload: ServerEvent;
      try {
        payload = JSON.parse(event.data) as ServerEvent;
      } catch {
        return;
      }
      if (payload.type === "tool_call") {
        pendingToolCallsRef.current.push({
          tool: payload.tool ?? "unknown",
          arguments: payload.arguments ?? {},
          result: payload.result ?? null,
          error: payload.error ?? null,
        });
      } else if (payload.type === "reply") {
        if (payload.conversation_id) {
          conversationIdRef.current = payload.conversation_id;
        }
        const reply: ChatMessage = {
          id: uid(),
          role: "assistant",
          content: payload.reply ?? "",
          toolCalls: pendingToolCallsRef.current,
          createdAt: new Date().toISOString(),
        };
        pendingToolCallsRef.current = [];
        setMessages((prev) => [...prev, reply]);
        setThinking(false);
      } else if (payload.type === "error") {
        setError(payload.error ?? "unknown error");
        setThinking(false);
      }
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [connect]);

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      const userMessage: ChatMessage = {
        id: uid(),
        role: "user",
        content: trimmed,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setError(null);
      setThinking(true);

      const ws = socketRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        setError("Not connected to the assistant. Reconnecting…");
        setThinking(false);
        connect();
        return;
      }
      ws.send(
        JSON.stringify({
          message: trimmed,
          conversation_id: conversationIdRef.current,
        }),
      );
    },
    [connect],
  );

  const reset = useCallback(() => {
    setMessages([]);
    conversationIdRef.current = null;
    pendingToolCallsRef.current = [];
    setError(null);
  }, []);

  return { messages, send, status, thinking, error, reset, connect };
}
