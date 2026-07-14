export type DashboardMetrics = {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_cost_usd: number;
  average_latency_ms: number;
  most_used_model: string | null;
  provider_error_counts: Record<string, number>;
  model_usage: Record<string, number>;
  fallback_rate: number;
  recent_requests: Array<{
    request_id: string;
    task_type: string;
    status: string;
    selected_model?: string;
    provider?: string;
    estimated_cost_usd?: number;
    latency_ms?: number;
    fallback_used?: boolean;
    requested_at?: string;
  }>;
};

export type AIModel = {
  id: string;
  provider_id: string;
  name: string;
  version: string;
  enabled: boolean;
  is_default: boolean;
  input_cost_per_million_tokens: number;
  output_cost_per_million_tokens: number;
  average_latency_ms: number;
  context_window: number;
  supports_vision: boolean;
  supports_documents: boolean;
  supports_structured_output: boolean;
  sensitive_data_allowed: boolean;
  languages: string[];
  quality_by_task: Record<string, number | Record<string, number>>;
  availability_pct: number;
  privacy_level: string;
};

export type InferenceListItem = {
  request_id: string;
  task_type: string;
  status: string;
  selected_model: string | null;
  estimated_cost_usd: number | null;
  latency_ms: number | null;
  requested_at: string;
};

export type InferenceDetail = {
  request_id: string;
  status: string;
  output: Record<string, unknown> | null;
  routing: {
    selected_model: string;
    provider: string;
    attempts: number;
    fallback_used: boolean;
    reason?: Record<string, unknown> | null;
  } | null;
  usage: {
    input_tokens: number;
    output_tokens: number;
    latency_ms: number;
    estimated_cost_usd: number;
  } | null;
  error: string | null;
};

export type EvaluationDataset = {
  id: string;
  name: string;
  task_type: string;
  version: string;
  description?: string | null;
  case_count: number;
};

export type EvaluationRun = {
  evaluation_id: string;
  dataset_id: string;
  status: string;
  model_ids: string[];
  update_model_quality: boolean;
  summary: {
    models?: Record<
      string,
      {
        accuracy: number;
        average_score: number;
        valid_json_rate: number;
        average_latency_ms: number;
        average_cost_usd: number;
        total_cost_usd: number;
        quality_by_difficulty?: Record<string, number>;
      }
    >;
    total_results?: number;
  };
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  result_count: number;
};

export type ClientProfile = {
  id: string;
  name: string;
  status: string;
  daily_budget_usd: number;
  requests_per_minute: number;
  created_at?: string | null;
  policies: Array<{
    task_type: string;
    strategy: string;
    minimum_quality: number;
    maximum_cost_usd: number;
    maximum_latency_ms: number;
    maximum_attempts: number;
    allow_fallback: boolean;
  }>;
  api_key_prefixes: string[];
};
