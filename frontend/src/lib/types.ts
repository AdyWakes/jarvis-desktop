export type Role = "user" | "assistant" | "system" | "tool";

export interface ToolCallRecord {
  tool: string;
  arguments: Record<string, unknown>;
  result: unknown;
  error?: string | null;
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  toolCalls?: ToolCallRecord[];
  createdAt: string;
}

export interface ToolDescriptor {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  enabled: boolean;
  source: string;
}

export interface SystemStatus {
  version: string;
  uptime_seconds: number;
  cpu_percent: number;
  memory_percent: number;
  openai_configured: boolean;
  tools: ToolDescriptor[];
}

export interface TaskItem {
  id: number;
  title: string;
  notes: string | null;
  status: "open" | "done";
  created_at: string;
  completed_at: string | null;
}

export interface TranscriptionResponse {
  text: string;
  duration: number | null;
  language: string | null;
}
