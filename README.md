# Intelligent AI Model Routing Platform

AI inference gateway that automatically selects the most cost-effective language model based on quality, latency, privacy and budget constraints. The platform supports model fallback, structured-output validation, provider failover, evaluation datasets, cost tracking and complete request observability.

> Repositorio: [FranLepGill/intelligent-model-router](https://github.com/FranLepGill/intelligent-model-router)

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [docs/STATUS.md](docs/STATUS.md) | **Todo lo implementado hasta ahora**, pendientes y decisiones |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Flujo, módulos y cómo extender providers |
| [docs/API.md](docs/API.md) | Contratos HTTP actuales |
| [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) | Resumen del brief de producto |

## Qué resuelve

Hoy muchas empresas mandan **todas** las consultas al mismo modelo. Esta plataforma actúa como infraestructura intermedia:

1. Recibe una solicitud normalizada (`POST /api/v1/inference`)
2. Extrae características deterministas
3. Filtra modelos incompatibles
4. Selecciona el modelo óptimo (costo / latencia / calidad)
5. Ejecuta, valida la respuesta y escala si falla
6. Registra costo, tokens, latencia y trazabilidad completa

No es un chatbot final: es un **gateway de inferencia** para otras aplicaciones.

## Stack (MVP)

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.12, FastAPI, Pydantic |
| Persistencia | PostgreSQL, SQLAlchemy, Alembic |
| Cache / rate limit | Redis |
| Providers | Adaptadores comunes + mocks (fase 1) |
| Frontend (próximo) | React + TypeScript |
| Infra | Docker Compose, GitHub Actions |

## Arranque rápido

### Requisitos

- Docker Desktop
- (Opcional) Python 3.12+ para desarrollo local

### Con Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

### Demo API key

Al iniciar con `SEED_DEMO_DATA=true` se crea:

```text
X-API-Key: imr_demo_key_change_me_in_production_abc123
```

### Ejemplo de inferencia

```bash
curl -X POST http://localhost:8000/api/v1/inference \
  -H "Content-Type: application/json" \
  -H "X-API-Key: imr_demo_key_change_me_in_production_abc123" \
  -d "{
    \"task_type\": \"customer_support\",
    \"input\": \"Me cobraron dos veces la factura 18392.\",
    \"language\": \"es\",
    \"priority\": \"normal\",
    \"max_cost_usd\": 0.05,
    \"max_latency_ms\": 5000,
    \"minimum_quality\": 0.85,
    \"contains_sensitive_data\": false,
    \"output_format\": \"json\"
  }"
```

### Forzar escenarios de demo

Incluí estos tokens en el `input` para simular fallos:

| Token en el input | Efecto |
|-------------------|--------|
| `FORCE_INVALID_JSON` | El modelo económico falla validación → fallback |
| `FORCE_PROVIDER_A_DOWN` | Caída de provider-a → usa provider-b |
| Texto largo / “contrato” / “compar” | Escalado a modelo más potente |

## API inicial (fase 1)

| Método | Path | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/inference` | Crear solicitud de inferencia |
| `GET` | `/api/v1/requests/{request_id}` | Consultar solicitud |
| `GET` | `/api/v1/requests` | Historial |
| `GET` | `/api/v1/models` | Listar modelos |
| `POST` | `/api/v1/models` | Registrar modelo |
| `PATCH` | `/api/v1/models/{model_id}` | Modificar modelo |
| `GET` | `/api/v1/health` | Healthcheck |

Headers opcionales:

- `Idempotency-Key`: evita ejecuciones duplicadas

## Arquitectura (monolito modular)

```text
Aplicación cliente
      ↓
API FastAPI
      ↓
Autenticación (API key hashed)
      ↓
Extracción de características
      ↓
Motor de routing
      ↓
Adaptador del proveedor
      ↓
Validación de respuesta
      ↓
Persistencia + métricas
      ↓
Respuesta normalizada
```

Módulos:

- `authentication` · `clients` · `models` · `providers`
- `routing` · `inference` · `validation`
- `evaluations` · `billing` · `observability` · `audit` (stubs / siguientes fases)

## Modelos seeded

| id | provider | rol |
|----|----------|-----|
| `model-small` | provider-a | Económico (default) |
| `model-medium` | provider-b | Avanzado / sensible |

## Desarrollo local (sin Docker para la app)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# levantar solo db/redis
docker compose up db redis -d

cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Tests

```bash
pytest -q
```

## Roadmap del MVP

1. **Fase 1 (hecha):** FastAPI, PostgreSQL, clientes, API keys, modelos, providers mock, `POST /inference`
2. **Fase 2–4 (parcial):** routing + validación + fallback + idempotencia hechos; faltan circuit breaker, rate limit Redis y adapters reales
3. **Fase 5:** datasets de evaluación (50–100 casos)
4. **Fase 6–7:** observabilidad + panel admin React
5. **Fase 8:** tests de carga, diagrama, demo pública

Detalle del avance: [docs/STATUS.md](docs/STATUS.md)

## Portfolio blurb

> Built an AI inference gateway that automatically selects the most cost-effective language model based on quality, latency, privacy and budget constraints. The platform supports model fallback, structured-output validation, provider failover, evaluation datasets, cost tracking and complete request observability.
