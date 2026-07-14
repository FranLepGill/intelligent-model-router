import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth";

export function LoginPage() {
  const { apiKey, setApiKey, demoKey } = useAuth();
  const [value, setValue] = useState(apiKey || demoKey);

  if (apiKey) {
    return <Navigate to="/" replace />;
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setApiKey(value);
  }

  return (
    <div className="login">
      <form className="login-card" onSubmit={onSubmit}>
        <h1>Model Router</h1>
        <p>
          Panel administrativo del inference gateway. Ingresá la API key del cliente
          para ver métricas, modelos y evaluaciones.
        </p>
        <input
          className="input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="imr_..."
          aria-label="API key"
        />
        <div className="toolbar">
          <button className="btn btn-primary" type="submit">
            Entrar
          </button>
          <button
            className="btn btn-secondary"
            type="button"
            onClick={() => setValue(demoKey)}
          >
            Usar demo key
          </button>
        </div>
      </form>
    </div>
  );
}
