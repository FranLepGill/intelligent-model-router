import { useCallback } from "react";
import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";

function qualityFor(model: { quality_by_task: Record<string, unknown> }) {
  const value = model.quality_by_task?.customer_support;
  return typeof value === "number" ? value.toFixed(3) : "—";
}

export function ModelsPage() {
  const loader = useCallback((key: string) => api.models(key), []);
  const { data, error, loading, reload } = useApiQuery(loader);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Modelos</h1>
          <p>Estado, costos, latencia y calidad observada por tarea.</p>
        </div>
        <button className="btn btn-secondary" onClick={() => void reload()} disabled={loading}>
          Actualizar
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Modelo</th>
                <th>Provider</th>
                <th>Estado</th>
                <th>Costo in/out</th>
                <th>Latencia</th>
                <th>Calidad CS</th>
                <th>Disponibilidad</th>
                <th>Privacidad</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map((model) => (
                <tr key={model.id}>
                  <td>
                    <div className="mono">{model.id}</div>
                    <div style={{ color: "var(--ink-soft)", fontSize: "0.85rem" }}>
                      {model.name}
                      {model.is_default ? " · default" : ""}
                    </div>
                  </td>
                  <td className="mono">{model.provider_id}</td>
                  <td>
                    <StatusBadge status={model.enabled ? "active" : "disabled"} />
                  </td>
                  <td className="mono">
                    ${model.input_cost_per_million_tokens}/
                    {model.output_cost_per_million_tokens}
                  </td>
                  <td className="mono">{model.average_latency_ms} ms</td>
                  <td className="mono">{qualityFor(model)}</td>
                  <td className="mono">{model.availability_pct}%</td>
                  <td>
                    <span className="badge badge-neutral">{model.privacy_level}</span>
                    {model.sensitive_data_allowed && (
                      <span className="badge badge-ok" style={{ marginLeft: 6 }}>
                        sensitive ok
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && !data?.length && <div className="empty">No hay modelos registrados.</div>}
        </div>
      </section>
    </>
  );
}
