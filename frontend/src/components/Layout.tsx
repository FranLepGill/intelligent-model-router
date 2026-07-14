import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/models", label: "Modelos" },
  { to: "/requests", label: "Solicitudes" },
  { to: "/evaluations", label: "Evaluaciones" },
  { to: "/clients", label: "Clientes" },
];

export function Layout() {
  const { apiKey } = useAuth();

  return (
    <div className="shell">
      <aside className="nav">
        <div className="brand">
          <div className="brand-mark">Model Router</div>
          <div className="brand-sub">Admin console</div>
        </div>
        <nav className="nav-links">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) => (isActive ? "active" : undefined)}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="nav-foot">
          Sesión con API key
          <div className="mono" style={{ marginTop: 6 }}>
            {apiKey.slice(0, 14)}…
          </div>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
