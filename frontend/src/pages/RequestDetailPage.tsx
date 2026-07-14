import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";

export function RequestDetailPage() {
  const { requestId = "" } = useParams();
  const loader = useCallback(
    (key: string) => api.requestDetail(key, requestId),
    [requestId],
  );
  const { data, error, loading, reload } = useApiQuery(loader);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Detalle de solicitud</h1>
          <p className="mono">{requestId}</p>
        </div>
        <div className="toolbar">
          <Link className="btn btn-secondary" to="/requests">
            Volver
          </Link>
          <button className="btn btn-secondary" onClick={() => void reload()} disabled={loading}>
            Actualizar
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="empty">Cargando…</div>}

      {data && (
        <div className="stack">
          <section className="panel">
            <h2>Resumen</h2>
            <div className="detail-grid">
              <div className="kv">
                <div className="k">Estado</div>
                <div className="v">
                  <StatusBadge status={data.status} />
                </div>
              </div>
              <div className="kv">
                <div className="k">Modelo</div>
                <div className="v">{data.routing?.selected_model ?? "—"}</div>
              </div>
              <div className="kv">
                <div className="k">Provider</div>
                <div className="v">{data.routing?.provider ?? "—"}</div>
              </div>
              <div className="kv">
                <div className="k">Intentos / fallback</div>
                <div className="v">
                  {data.routing?.attempts ?? 0} / {data.routing?.fallback_used ? "sí" : "no"}
                </div>
              </div>
              <div className="kv">
                <div className="k">Costo</div>
                <div className="v">
                  {data.usage
                    ? `$${data.usage.estimated_cost_usd.toFixed(6)}`
                    : "—"}
                </div>
              </div>
              <div className="kv">
                <div className="k">Latencia / tokens</div>
                <div className="v">
                  {data.usage
                    ? `${data.usage.latency_ms} ms · ${data.usage.input_tokens}/${data.usage.output_tokens}`
                    : "—"}
                </div>
              </div>
            </div>
            {data.error && (
              <p style={{ color: "var(--bad)", marginBottom: 0 }}>Error: {data.error}</p>
            )}
          </section>

          <div className="split">
            <section className="panel">
              <h2>Respuesta</h2>
              <pre className="json">{JSON.stringify(data.output, null, 2) ?? "null"}</pre>
            </section>
            <section className="panel">
              <h2>Decisión de routing</h2>
              <pre className="json">
                {JSON.stringify(data.routing?.reason ?? data.routing, null, 2)}
              </pre>
            </section>
          </div>
        </div>
      )}
    </>
  );
}
