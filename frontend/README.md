# Model Router Admin

Panel administrativo React + TypeScript para el Intelligent AI Model Routing Platform.

## Pantallas

- **Dashboard** — KPIs, uso por modelo, errores por provider
- **Modelos** — costos, latencia, calidad, disponibilidad
- **Solicitudes** — historial y detalle (routing + output)
- **Evaluaciones** — datasets, correr eval, comparar modelos
- **Clientes** — límites, políticas y API key de sesión

## Desarrollo

```bash
npm install
npm run dev
```

Proxy Vite: `/api` → `http://localhost:8000`

Demo key por defecto: `imr_demo_key_change_me_in_production_abc123`

## Docker

Servicio `admin` en `docker-compose.yml` (nginx en puerto **5173**, proxy a la API).
