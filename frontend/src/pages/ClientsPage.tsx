import { useCallback, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth";
import { StatusBadge } from "../components/StatusBadge";
import { useApiQuery } from "../hooks/useApiQuery";

export function ClientsPage() {
  const navigate = useNavigate();
  const { apiKey, setApiKey, clearApiKey, demoKey } = useAuth();
  const [draft, setDraft] = useState(apiKey);
  const loader = useCallback((key: string) => api.me(key), []);
  const { data, error, loading, reload } = useApiQuery(loader);

  function onSave(event: FormEvent) {
    event.preventDefault();
    setApiKey(draft);
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Clientes</h1>
          <p>Estado, límites, presupuestos, políticas y API keys del cliente actual.</p>
        </div>
        <button className="btn btn-secondary" onClick={() => void reload()} disabled={loading}>
          Actualizar
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="split">
        <section className="panel">
          <h2>Cliente autenticado</h2>
          {data ? (
            <div className="detail-grid">
              <div className="kv">
                <div className="k">Nombre</div>
                <div className="v">{data.name}</div>
              </div>
              <div className="kv">
                <div className="k">Estado</div>
                <div className="v">
                  <StatusBadge status={data.status} />
                </div>
              </div>
              <div className="kv">
                <div className="k">Presupuesto diario</div>
                <div className="v">${data.daily_budget_usd}</div>
              </div>
              <div className="kv">
                <div className="k">RPM</div>
                <div className="v">{data.requests_per_minute}</div>
              </div>
              <div className="kv">
                <div className="k">API key prefixes</div>
                <div className="v">{data.api_key_prefixes.join(", ") || "—"}</div>
              </div>
              <div className="kv">
                <div className="k">Creado</div>
                <div className="v">{data.created_at ?? "—"}</div>
              </div>
            </div>
          ) : (
            <div className="empty">{loading ? "Cargando…" : "Sin datos"}</div>
          )}
        </section>

        <section className="panel">
          <h2>Credencial de sesión</h2>
          <form onSubmit={onSave}>
            <input
              className="input"
              style={{ width: "100%", borderRadius: 14, marginBottom: "0.8rem" }}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
            />
            <div className="toolbar">
              <button className="btn btn-primary" type="submit">
                Guardar key
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => {
                  setDraft(demoKey);
                  setApiKey(demoKey);
                }}
              >
                Demo key
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => {
                  clearApiKey();
                  setDraft("");
                  navigate("/login");
                }}
              >
                Salir
              </button>
            </div>
          </form>
        </section>
      </div>

      <section className="panel" style={{ marginTop: "1rem" }}>
        <h2>Políticas habilitadas</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Task</th>
                <th>Strategy</th>
                <th>Min quality</th>
                <th>Max cost</th>
                <th>Max latency</th>
                <th>Attempts</th>
                <th>Fallback</th>
              </tr>
            </thead>
            <tbody>
              {(data?.policies ?? []).map((policy) => (
                <tr key={policy.task_type}>
                  <td className="mono">{policy.task_type}</td>
                  <td>{policy.strategy}</td>
                  <td className="mono">{policy.minimum_quality}</td>
                  <td className="mono">${policy.maximum_cost_usd}</td>
                  <td className="mono">{policy.maximum_latency_ms} ms</td>
                  <td className="mono">{policy.maximum_attempts}</td>
                  <td>{policy.allow_fallback ? "sí" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.policies?.length && !loading && (
            <div className="empty">Este cliente no tiene políticas cargadas.</div>
          )}
        </div>
      </section>
    </>
  );
}
