import { useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";

export function RequestsPage() {
  const loader = useCallback((key: string) => api.requests(key, 100), []);
  const { data, error, loading, reload } = useApiQuery(loader);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Solicitudes</h1>
          <p>Historial de inferencias con modelo, costo y latencia.</p>
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
                <th>Request</th>
                <th>Tarea</th>
                <th>Estado</th>
                <th>Modelo</th>
                <th>Costo</th>
                <th>Latencia</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map((row) => (
                <tr key={row.request_id}>
                  <td>
                    <Link className="mono" to={`/requests/${row.request_id}`}>
                      {row.request_id}
                    </Link>
                  </td>
                  <td>{row.task_type}</td>
                  <td>
                    <StatusBadge status={row.status} />
                  </td>
                  <td className="mono">{row.selected_model ?? "—"}</td>
                  <td className="mono">
                    {row.estimated_cost_usd != null
                      ? `$${row.estimated_cost_usd.toFixed(6)}`
                      : "—"}
                  </td>
                  <td className="mono">
                    {row.latency_ms != null ? `${row.latency_ms} ms` : "—"}
                  </td>
                  <td className="mono">{row.requested_at || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && !data?.length && (
            <div className="empty">
              Sin solicitudes. Enviá una con{" "}
              <code className="mono">POST /api/v1/inference</code>.
            </div>
          )}
        </div>
      </section>
    </>
  );
}
