import { useCallback, useState } from "react";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth";
import { StatusBadge } from "../components/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";

export function EvaluationsPage() {
  const { apiKey } = useAuth();
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [lastRunId, setLastRunId] = useState<string | null>(null);

  const datasetsLoader = useCallback((key: string) => api.datasets(key), []);
  const runsLoader = useCallback((key: string) => api.evaluations(key), []);
  const datasets = useApiQuery(datasetsLoader);
  const runs = useApiQuery(runsLoader);

  async function runEvaluation() {
    setRunning(true);
    setRunError(null);
    try {
      const result = await api.runEvaluation(apiKey);
      setLastRunId(result.evaluation_id);
      await runs.reload();
      await datasets.reload();
    } catch (err) {
      setRunError(err instanceof ApiError ? err.message : "Falló la evaluación");
    } finally {
      setRunning(false);
    }
  }

  const latest = runs.data?.[0];

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Evaluaciones</h1>
          <p>Datasets, comparación de modelos y calidad medida.</p>
        </div>
        <div className="toolbar">
          <button
            className="btn btn-primary"
            onClick={() => void runEvaluation()}
            disabled={running || !apiKey}
          >
            {running ? "Ejecutando…" : "Correr evaluación"}
          </button>
          <button className="btn btn-secondary" onClick={() => void runs.reload()}>
            Actualizar
          </button>
        </div>
      </div>

      {(datasets.error || runs.error || runError) && (
        <div className="error-banner">{runError || datasets.error || runs.error}</div>
      )}
      {lastRunId && (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          Última corrida lanzada: <span className="mono">{lastRunId}</span>
        </div>
      )}

      <div className="split">
        <section className="panel">
          <h2>Datasets</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Nombre</th>
                  <th>Tarea</th>
                  <th>Casos</th>
                </tr>
              </thead>
              <tbody>
                {(datasets.data ?? []).map((ds) => (
                  <tr key={ds.id}>
                    <td className="mono">{ds.id}</td>
                    <td>{ds.name}</td>
                    <td>{ds.task_type}</td>
                    <td className="mono">{ds.case_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel">
          <h2>Comparación (última corrida)</h2>
          {latest?.summary?.models ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Modelo</th>
                    <th>Accuracy</th>
                    <th>Score</th>
                    <th>JSON válido</th>
                    <th>Latencia</th>
                    <th>Costo avg</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(latest.summary.models).map(([modelId, metrics]) => (
                    <tr key={modelId}>
                      <td className="mono">{modelId}</td>
                      <td className="mono">{(metrics.accuracy * 100).toFixed(1)}%</td>
                      <td className="mono">{metrics.average_score.toFixed(3)}</td>
                      <td className="mono">{(metrics.valid_json_rate * 100).toFixed(1)}%</td>
                      <td className="mono">{metrics.average_latency_ms.toFixed(0)} ms</td>
                      <td className="mono">${metrics.average_cost_usd.toFixed(6)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty">
              Todavía no hay corridas. Presioná “Correr evaluación” (puede tardar ~10–20s con
              80 casos × 2 modelos).
            </div>
          )}
        </section>
      </div>

      <section className="panel" style={{ marginTop: "1rem" }}>
        <h2>Historial de corridas</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Dataset</th>
                <th>Estado</th>
                <th>Modelos</th>
                <th>Inicio</th>
              </tr>
            </thead>
            <tbody>
              {(runs.data ?? []).map((run) => (
                <tr key={run.evaluation_id}>
                  <td className="mono">{run.evaluation_id}</td>
                  <td className="mono">{run.dataset_id}</td>
                  <td>
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="mono">{run.model_ids.join(", ")}</td>
                  <td className="mono">{run.started_at ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
