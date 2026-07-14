import { useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";

function money(value: number) {
  return `$${value.toFixed(6)}`;
}

export function DashboardPage() {
  const loader = useCallback((key: string) => api.metrics(key), []);
  const { data, error, loading, reload } = useApiQuery(loader);

  const maxUsage = Math.max(1, ...Object.values(data?.model_usage ?? { _: 1 }));
  const topErrorProvider =
    data && Object.keys(data.provider_error_counts).length
      ? Object.entries(data.provider_error_counts).sort((a, b) => b[1] - a[1])[0]
      : null;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p>Vista general de costo, latencia, fallos y uso por modelo.</p>
        </div>
        <div className="toolbar">
          <button className="btn btn-secondary" onClick={() => void reload()} disabled={loading}>
            Actualizar
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-metrics">
        <div className="metric">
          <div className="label">Solicitudes totales</div>
          <div className="value">{data?.total_requests ?? "—"}</div>
        </div>
        <div className="metric">
          <div className="label">Exitosas / fallidas</div>
          <div className="value">
            {data ? `${data.successful_requests}/${data.failed_requests}` : "—"}
          </div>
        </div>
        <div className="metric">
          <div className="label">Costo total</div>
          <div className="value">{data ? money(data.total_cost_usd) : "—"}</div>
        </div>
        <div className="metric">
          <div className="label">Latencia promedio</div>
          <div className="value">
            {data ? `${data.average_latency_ms.toFixed(0)} ms` : "—"}
          </div>
        </div>
      </div>

      <div className="split">
        <section className="panel">
          <h2>Modelo más utilizado</h2>
          {loading && <div className="empty">Cargando…</div>}
          {!loading && (
            <>
              <p className="mono" style={{ marginTop: 0 }}>
                {data?.most_used_model ?? "Sin datos aún"}
              </p>
              <div className="bars" style={{ marginTop: "1rem" }}>
                {Object.entries(data?.model_usage ?? {}).map(([model, count]) => (
                  <div className="bar-row" key={model}>
                    <span className="mono">{model}</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{ width: `${(count / maxUsage) * 100}%` }}
                      />
                    </div>
                    <span>{count}</span>
                  </div>
                ))}
                {!Object.keys(data?.model_usage ?? {}).length && (
                  <div className="empty">
                    Todavía no hay inferencias. Probá{" "}
                    <Link to="/requests">crear tráfico</Link> vía API.
                  </div>
                )}
              </div>
              <p style={{ color: "var(--ink-soft)", marginBottom: 0 }}>
                Fallback rate: {data ? `${(data.fallback_rate * 100).toFixed(1)}%` : "—"}
              </p>
            </>
          )}
        </section>

        <section className="panel">
          <h2>Proveedor con más errores</h2>
          {topErrorProvider ? (
            <>
              <p className="mono" style={{ marginTop: 0 }}>
                {topErrorProvider[0]}
              </p>
              <p>
                {topErrorProvider[1]} solicitud(es) fallidas atribuidas a este provider.
              </p>
              <div className="bars">
                {Object.entries(data?.provider_error_counts ?? {}).map(([provider, count]) => (
                  <div className="bar-row" key={provider}>
                    <span className="mono">{provider}</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${(count / Math.max(topErrorProvider[1], 1)) * 100}%`,
                          background: "linear-gradient(90deg, #9b2c2c, #c45c26)",
                        }}
                      />
                    </div>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty">Sin errores de proveedor en la ventana reciente.</div>
          )}
        </section>
      </div>

      <section className="panel" style={{ marginTop: "1rem" }}>
        <h2>Solicitudes recientes</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Estado</th>
                <th>Modelo</th>
                <th>Costo</th>
                <th>Latencia</th>
                <th>Fallback</th>
              </tr>
            </thead>
            <tbody>
              {(data?.recent_requests ?? []).map((row) => (
                <tr key={row.request_id}>
                  <td>
                    <Link className="mono" to={`/requests/${row.request_id}`}>
                      {row.request_id}
                    </Link>
                  </td>
                  <td>
                    <StatusBadge status={row.status} />
                  </td>
                  <td className="mono">{row.selected_model ?? "—"}</td>
                  <td className="mono">
                    {row.estimated_cost_usd != null ? money(row.estimated_cost_usd) : "—"}
                  </td>
                  <td className="mono">
                    {row.latency_ms != null ? `${row.latency_ms} ms` : "—"}
                  </td>
                  <td>{row.fallback_used ? "sí" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.recent_requests?.length && !loading && (
            <div className="empty">Sin solicitudes todavía.</div>
          )}
        </div>
      </section>
    </>
  );
}
