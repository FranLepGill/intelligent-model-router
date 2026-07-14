import type {
  AIModel,
  ClientProfile,
  DashboardMetrics,
  EvaluationDataset,
  EvaluationRun,
  InferenceDetail,
  InferenceListItem,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  apiKey: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, String(detail));
  }

  return response.json() as Promise<T>;
}

export const api = {
  metrics: (apiKey: string) =>
    request<DashboardMetrics>("/api/v1/admin/metrics", apiKey),
  me: (apiKey: string) => request<ClientProfile>("/api/v1/me", apiKey),
  models: (apiKey: string) => request<AIModel[]>("/api/v1/models", apiKey),
  requests: (apiKey: string, limit = 100) =>
    request<InferenceListItem[]>(`/api/v1/requests?limit=${limit}`, apiKey),
  requestDetail: (apiKey: string, id: string) =>
    request<InferenceDetail>(`/api/v1/requests/${id}`, apiKey),
  datasets: (apiKey: string) =>
    request<EvaluationDataset[]>("/api/v1/evaluations/datasets", apiKey),
  evaluations: (apiKey: string) =>
    request<EvaluationRun[]>("/api/v1/evaluations?limit=20", apiKey),
  runEvaluation: (apiKey: string, datasetId = "customer-support-v1") =>
    request<EvaluationRun>("/api/v1/evaluations/run", apiKey, {
      method: "POST",
      body: JSON.stringify({
        dataset_id: datasetId,
        update_model_quality: true,
      }),
    }),
};
