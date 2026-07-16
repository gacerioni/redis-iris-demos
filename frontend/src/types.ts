export type ChatRole = "user" | "assistant";

export type ToolEvent = {
  toolName: string;
  toolKind: "internal_function" | "mcp_tool" | "memory" | "langcache" | "guardrail";
  status: "call" | "result";
  payload: Record<string, unknown>;
  durationMs?: number;
  ts?: number;
};

export type MergedToolEvent = {
  toolName: string;
  toolKind: ToolEvent["toolKind"];
  callPayload?: Record<string, unknown>;
  resultPayload?: Record<string, unknown>;
  durationMs?: number;
  ts?: number;
};

export type ThinkingStep = {
  id: string;
  text: string;
  ts: number;
  kind: "plan" | "llm";
  durationMs?: number;
  durationText?: string;
};

export type StatusMessage = { text: string; ts: number };

export type DoneMeta = {
  cacheHit?: boolean;
  guardrailBlocked?: boolean;
  tokensIn?: number;
  tokensOut?: number;
  tokensSavedEst?: number;
  totalElapsedMs?: number;
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  statusMessages: StatusMessage[];
  thinkingSteps: ThinkingStep[];
  toolEvents: ToolEvent[];
  doneMeta?: DoneMeta;
};

export type HealthState = {
  ok: boolean;
  domain: string;
  mcp_enabled: boolean;
  memory_enabled?: boolean;
  langcache_enabled?: boolean;
  internal_tools: string[];
} | null;

export type MemoryDashboardState = {
  enabled: boolean;
  thread_id?: string | null;
  owner_id?: string;
  short_term: Array<Record<string, unknown>>;
  long_term: Array<Record<string, unknown>>;
  errors?: string[];
} | null;

export type AgentMode = "context_surfaces" | "simple_rag";

export type PromptCard = { eyebrow: string; title: string; prompt: string; featured?: boolean };

export type UiConfig = {
  show_platform_surface?: boolean;
  show_live_updates?: boolean;
  platform_surface_eyebrow?: string;
  platform_surface_title?: string;
  platform_data_planes?: string[];
  live_updates_eyebrow?: string;
  live_updates_title?: string;
};

export type DomainConfig = {
  id: string;
  app_name: string;
  subtitle: string;
  hero_title: string;
  placeholder_text: string;
  demo_steps: string[];
  starter_prompts: PromptCard[];
  theme: Record<string, string>;
  logo_src: string;
  ui?: UiConfig;
  seed_langcache?: { prompt: string; response: string }[];
} | null;

export type ToolDefinition = {
  name: string;
  description: string;
  kind: "internal" | "mcp_tool";
  input_schema?: Record<string, unknown>;
};

export type ToolsResponse = {
  tools: ToolDefinition[];
  count: number;
};

export type RedisContextView = "activity" | "redis-context" | "finops";

export type LatencyStats = { p50: number; p95: number; samples: number };

export type FinOpsSummary = {
  turns: number;
  cache_hits: number;
  llm_turns: number;
  blocked: number;
  hit_rate: number;
  tokens_in: number;
  tokens_out: number;
  saved_in: number;
  saved_out: number;
  avg_tokens_in_per_llm_turn: number;
  avg_tokens_out_per_llm_turn: number;
  latency_hit_ms: LatencyStats;
  latency_llm_ms: LatencyStats;
  latency_lookup_ms: LatencyStats;
  slice_calls: number;
  slice_full_tokens: number;
  slice_served_tokens: number;
};
