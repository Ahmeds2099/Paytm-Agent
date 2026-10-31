export type VoiceState =
  | "idle"
  | "connecting"
  | "waking_up"
  | "listening"
  | "thinking"
  | "speaking"
  | "interrupted"
  | "fallback"
  | "error";

export type Provenance = "document" | "general" | "not_in_source";

export type PipelineStageName =
  | "microphone"
  | "stt"
  | "memory"
  | "retrieval"
  | "llm"
  | "emotion"
  | "tts"
  | "playback"
  | "intent"
  | "tool_action";

export type PipelineStage = {
  responseId?: string;
  stage: PipelineStageName;
  status: string;
  durationMs?: number;
  elapsedMs?: number;
  clientElapsedMs?: number;
  updatedAt: number;
};

// Phase 4: tool call record from the backend
export type ToolCall = {
  tool: string;
  args: Record<string, unknown>;
  status: "ok" | "not_found" | "error";
  latency_ms: number;
  ts: number;
};

// Phase 4: escalation event from the backend
export type EscalationEvent = {
  reason: string;
  ts: number;
};


export type SourceReference = {
  filename?: string;
  location_type?: string;
  location_value?: string | number;
  score?: number;
};

export type TurnContext = {
  responseId: string;
  provenance: Provenance;
  memoryCount: number;
  documentCount: number;
  sources: SourceReference[];
};

export type TurnMetrics = {
  responseId: string;
  serverResponseMs?: number;
  estimatedOutputTokens?: number;
  interrupted?: boolean;
};

export type ProviderState = "configured" | "active" | "ready" | "degraded" | "missing" | "unavailable" | "loading";

export type ProviderHealth = {
  name: string;
  status: ProviderState | string;
};

export type ConversationTurn = {
  id: string;
  role: "user" | "assistant";
  text: string;
  interim?: boolean;
  interrupted?: boolean;
  provenance?: Provenance;
  sources?: SourceReference[];
  memoryCount?: number;
  emotionLabel?: string;
  emotionAdapted?: boolean;
  metrics?: TurnMetrics;
  createdAt: number;
};

export type DomainProfile = {
  domain: string;
  professional_role: string;
  description: string;
  confidence: number;
  safety_category: string;
};

export type UploadedDocument = {
  document_id: string;
  filename: string;
  source_type: string;
  chunks: number;
  domain_profile: DomainProfile;
  demo_slug?: string;
};

export type DemoDocument = {
  slug: string;
  filename: string;
  title: string;
  description: string;
  format: "PDF" | "CSV" | "JSON";
};

export type DemoMerchant = {
  merchant_id: string;
  name: string;
  business_name: string;
  city: string;
  phone: string;
  language: string;
  language_display: string;
  avatar: string;
  scenario_id: string;
  scenario_label: string;
  scenario_description: string;
  member_since: string;
  total_transactions: number;
  account_balance: string;
  open_tickets: number;
  transaction_id?: string | null;
  transaction_amount?: number | null;
  transaction_status?: string | null;
  transaction_date?: string | null;
  expected_date?: string | null;
  device_id?: string | null;
  recommended?: boolean;
  opted_out?: boolean;
};

export type SystemStatus = {
  app: string;
  version: string;
  environment: string;
  status: string;
  persistence: string;
  providers: Record<string, string | Record<string, unknown>>;
  settings?: {
    tools_enabled: boolean;
    emotion_enabled: boolean;
    mode: "local" | "lite";
    tts_provider?: "cartesia" | "sarvam";
    tts_model?: string;
  };
};
