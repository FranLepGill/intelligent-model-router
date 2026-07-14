# Estado del proyecto — Intelligent AI Model Routing Platform

**Fecha:** 14 de julio de 2026  
**Repositorio:** https://github.com/FranLepGill/intelligent-model-router  
**Cuenta GitHub:** `FranLepGill`  
**Nombre del repo:** `intelligent-model-router`  
**Fase actual:** Fase 1–4 parcial + **Fase 5 (evaluaciones)** completada

---

## 1. Resumen ejecutivo

Se inicializó el proyecto como un **monolito modular** en FastAPI que actúa como gateway de inferencia. La plataforma:

- Autentica clientes por API key
- Recibe solicitudes normalizadas en `POST /api/v1/inference`
- Extrae características deterministas
- Selecciona un modelo (por defecto el económico; luego por scoring)
- Ejecuta contra adapters de proveedor
- Valida la respuesta estructurada
- Escala / hace fallback si falla
- Persiste request, intentos, costo, tokens y latencia

**Importante:** hoy los proveedores son **mocks locales**. No hay conexión real a OpenAI, Anthropic u otro vendor.

---

## 2. Trabajo realizado (checklist)

### 2.1 Infraestructura y repositorio

| Ítem | Estado | Notas |
|------|--------|-------|
| Repo GitHub público | Hecho | `FranLepGill/intelligent-model-router` |
| Rama `main` + push inicial | Hecho | 3 commits |
| Docker + Docker Compose | Hecho | API, PostgreSQL 16, Redis 7 |
| Dockerfile Python 3.12 | Hecho | |
| `.env.example` / secrets fuera del código | Hecho | |
| `.gitignore` | Hecho | |
| GitHub Actions CI | Hecho | tests unitarios + ruff |
| README de arranque | Hecho | |
| Spec del producto en `docs/` | Hecho | |

### 2.2 Backend — Fase 1

| Ítem | Estado | Ubicación |
|------|--------|-----------|
| Proyecto FastAPI | Hecho | `app/main.py` |
| Configuración tipada (Pydantic Settings) | Hecho | `app/config.py` |
| PostgreSQL + SQLAlchemy async | Hecho | `app/db.py` |
| Migración inicial Alembic | Hecho | `alembic/versions/001_initial_schema.py` |
| Clientes (`Client`) | Hecho | `app/models/entities.py` |
| API keys (hash SHA-256, no plaintext) | Hecho | `app/modules/authentication/` |
| Registro de providers | Hecho | tabla `model_providers` |
| Registro de modelos AI | Hecho | tabla `ai_models` + API |
| Políticas de routing por cliente/tarea | Hecho | tabla `routing_policies` |
| Seed de datos demo | Hecho | `app/seed.py` |

### 2.3 Inferencia y routing (Fase 2–4 parcial)

| Ítem | Estado | Notas |
|------|--------|-------|
| `POST /api/v1/inference` | Hecho | Primera historia de usuario |
| Validación Pydantic del request | Hecho | `app/schemas/inference.py` |
| Verificación de API key (`X-API-Key`) | Hecho | |
| Persistencia de `InferenceRequest` | Hecho | |
| Persistencia de `InferenceAttempt` | Hecho | |
| Extracción de features deterministas | Hecho | tokens, longitud, complejidad, sensible, etc. |
| Filtro de modelos incompatibles | Hecho | costo, latencia, vision, sensible, contexto |
| Scoring (cheapest / fastest / quality_first / balanced) | Hecho | `RoutingEngine` |
| Explicación de la decisión (`routing.reason`) | Hecho | incluye descartados |
| Adaptador común de proveedor | Hecho | `ProviderAdapter` |
| Mock provider-a (económico) | Hecho | `MockProviderAAdapter` |
| Mock provider-b (avanzado) | Hecho | `MockProviderBAdapter` |
| Normalización / validación de JSON | Hecho | categorías customer_support |
| Fallback / escalado a modelo más potente | Hecho | máximo de intentos desde política |
| Fallback si el proveedor cae | Hecho | simulado con tokens `FORCE_*` |
| Idempotencia (`Idempotency-Key`) | Hecho | unique por cliente |
| Latencia / tokens / costo estimado | Hecho | guardados en `usage` |
| `GET /api/v1/requests/{id}` | Hecho | |
| `GET /api/v1/requests` | Hecho | historial |
| CRUD parcial de modelos | Hecho | GET / POST / PATCH |

### 2.4 Evaluaciones — Fase 5

| Ítem | Estado | Notas |
|------|--------|-------|
| Tablas evaluation_* | Hecho | migración `002` |
| Dataset 80 casos customer_support | Hecho | seed `customer-support-v1` |
| Categorías demo (5) | Hecho | 16 casos c/u approx |
| Dificultades easy/medium/hard | Hecho | 37 / 33 / 10 |
| `POST /evaluations/run` | Hecho | compara modelos |
| Métricas + summary | Hecho | accuracy, JSON, costo, latencia |
| Update `quality_by_task` | Hecho | blend 30/70 hacia router |
| GET datasets / results | Hecho | |

### 2.5 Testing

| Ítem | Estado |
|------|--------|
| Tests unitarios auth | Hecho (`tests/test_auth.py`) |
| Tests unitarios routing | Hecho (`tests/test_routing.py`) |
| Tests unitarios validation | Hecho (`tests/test_validation.py`) |
| Tests unitarios evaluations | Hecho (`tests/test_evaluations.py`) |
| 13 tests passing en CI | Hecho |
| Tests de integración con DB | Pendiente |
| Tests de carga (k6/Locust) | Pendiente |

---

## 3. Commits en GitHub

| Commit | Mensaje |
|--------|---------|
| `001a16d` | Initialize intelligent-model-router MVP foundation |
| `6020d03` | Omit GitHub Actions until the local token has workflow scope |
| `d7aeed8` | Restore GitHub Actions CI workflow now that the token has workflow scope |

---

## 4. Estructura del código

```text
intelligent-model-router/
├── app/
│   ├── main.py                 # FastAPI app + lifespan (seed)
│   ├── config.py               # Settings
│   ├── db.py                   # Engine / session async
│   ├── seed.py                 # Demo client, keys, models
│   ├── api/v1/                 # HTTP routers
│   │   ├── health.py
│   │   ├── inference.py
│   │   └── models.py
│   ├── models/entities.py      # SQLAlchemy ORM
│   ├── schemas/                # Pydantic request/response
│   └── modules/                # Monolito modular
│       ├── authentication/     # Hash + validate API keys
│       ├── providers/          # Adapter interface + mocks
│       ├── routing/            # Features + scoring engine
│       ├── inference/          # Orquestación end-to-end
│       ├── validation/         # Validación de respuesta
│       ├── evaluations/        # Stub (fase 5)
│       ├── billing/            # Stub
│       ├── observability/      # Stub
│       └── audit/              # Stub
├── alembic/                    # Migraciones
├── tests/                      # Pytest
├── docs/                       # Documentación
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .github/workflows/ci.yml
```

---

## 5. Modelo de datos implementado

| Entidad | Tabla | Propósito |
|---------|-------|-----------|
| `Client` | `clients` | Aplicación cliente |
| `ApiKey` | `api_keys` | Credenciales (solo hash) |
| `ModelProvider` | `model_providers` | Proveedor lógico |
| `AIModel` | `ai_models` | Modelo con costos/capacidades/calidad |
| `RoutingPolicy` | `routing_policies` | Política por `task_type` |
| `InferenceRequest` | `inference_requests` | Solicitud + features + usage + output |
| `InferenceAttempt` | `inference_attempts` | Cada intento a un modelo |

**Aún no implementadas como tablas** (previsto en fases siguientes):

- `EvaluationDataset` / `EvaluationCase` / `EvaluationResult`
- Circuit breaker persistido
- Rate-limit counters (Redis preparado en Compose pero aún no cableado en app)
- Audit log estructurado

---

## 6. Providers actuales

| Provider ID | Adapter real | Rol |
|-------------|--------------|-----|
| `provider-a` | `MockProviderAAdapter` | Modelo económico; puede fallar JSON en prompts complejos |
| `provider-b` | `MockProviderBAdapter` | Modelo avanzado; mayor latencia/costo simulados |

Configuración:

- `USE_MOCK_PROVIDERS=true` (default)
- `PROVIDER_A_API_KEY` / `PROVIDER_B_API_KEY` vacíos

Tokens de demo en el `input`:

| Token | Comportamiento |
|-------|----------------|
| `FORCE_INVALID_JSON` | Fallo de validación → fallback |
| `FORCE_PROVIDER_A_DOWN` | Caída de provider-a |
| `FORCE_PROVIDER_B_DOWN` | Timeout de provider-b |

---

## 7. Datos seed (demo)

| Recurso | Valor |
|---------|-------|
| Cliente | `demo-customer-support` |
| API key | `imr_demo_key_change_me_in_production_abc123` |
| Modelo default | `model-small` (provider-a) |
| Modelo avanzado | `model-medium` (provider-b) |
| Política | `customer_support` → strategy `balanced`, quality ≥ 0.85 |

Clasificación demo (categorías):

- `password_problem`
- `duplicate_charge`
- `refund_problem`
- `account_blocked`
- `general_question`

---

## 8. API disponible hoy

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/` | No | Info básica |
| `GET` | `/api/v1/health` | No | Healthcheck |
| `POST` | `/api/v1/inference` | API key | Inferencia con routing |
| `GET` | `/api/v1/requests/{request_id}` | API key | Detalle |
| `GET` | `/api/v1/requests` | API key | Historial |
| `GET` | `/api/v1/models` | API key | Listar modelos |
| `POST` | `/api/v1/models` | API key | Registrar modelo |
| `PATCH` | `/api/v1/models/{model_id}` | API key | Actualizar modelo |

**Headers**

- `X-API-Key` (requerido en endpoints protegidos)
- `Idempotency-Key` (opcional en inference)

**Swagger:** http://localhost:8000/docs

---

## 9. Criterios de aceptación de la primera HU

Historia: *Como aplicación cliente, quiero enviar una consulta a través de una API común…*

| Criterio | Estado |
|----------|--------|
| Existe `POST /api/v1/inference` | Cumple |
| Validación con Pydantic | Cumple |
| Se verifica la API key | Cumple |
| Se crea registro en DB | Cumple |
| Se selecciona modelo default inicialmente | Cumple (`is_default` / `model-small`) |
| Se envía al proveedor | Cumple (mock) |
| Se almacena latencia | Cumple |
| Se almacenan tokens | Cumple |
| Se almacena costo estimado | Cumple |
| Se devuelve identificador único | Cumple (`req_…`) |
| Errores del proveedor controlados | Cumple |

---

## 10. Pendiente (respecto al brief del MVP)

### Corto plazo (Fases 2–4 restantes)

- [ ] Adapters HTTP reales (2 providers, p. ej. OpenAI + Anthropic / otro)
- [ ] Circuit breaker (closed / open / half-open)
- [ ] Rate limiting real con Redis (RPM, concurrentes, presupuesto diario)
- [ ] Enmascarado de datos sensibles en logs
- [ ] Endpoints de routing policies (`POST /api/v1/routing-policies`)

### Fase 5 — Evaluaciones

- [x] Datasets + casos (80 consultas `customer-support-v1`)
- [x] Tablas `evaluation_datasets|cases|runs|results` + migración `002`
- [x] `POST /api/v1/evaluations/run` + GET resultados/datasets
- [x] Métricas (accuracy, JSON válido, costo, latencia, por dificultad/idioma)
- [x] Actualización de `quality_by_task` usada por el router

### Fase 6 — Observabilidad

- [ ] OpenTelemetry traces
- [ ] Métricas Prometheus
- [ ] Dashboard Grafana
- [ ] Logs estructurados sin secretos

### Fase 7 — Panel admin (React + TypeScript)

- [ ] Dashboard (requests, costo, latencia)
- [ ] Historial, modelos, evaluaciones, clientes, políticas

### Fase 8 — Calidad final

- [ ] Tests de integración / Testcontainers
- [ ] Pruebas de carga
- [ ] Diagrama de arquitectura publicado
- [ ] Video demo + deployment público

### Explicitamente fuera de alcance v1

Fine-tuning, chatbot completo, billing real a clientes, Kubernetes, microservicios, ML para routing, audio/video, multi-región.

---

## 11. Cómo reproducir el estado actual

```bash
git clone https://github.com/FranLepGill/intelligent-model-router.git
cd intelligent-model-router
cp .env.example .env
docker compose up --build
```

Tests locales:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
pytest -q
```

---

## 12. Decisiones técnicas tomadas

1. **Monolito modular** (no microservicios), según el brief.
2. **Providers detrás de una interfaz común** para no acoplar el motor de routing.
3. **Mocks primero** para poder desarrollar y demos sin API keys de pago.
4. **API keys hasheadas** (SHA-256); nunca se guardan en claro.
5. **Primera selección = modelo default**; intentos siguientes usan scoring + exclusión de modelos ya usados (escalado).
6. **Idempotencia** a nivel DB (`client_id` + `idempotency_key`).
7. **CI mínimo** en GitHub Actions (pytest + ruff) desde el día 1.

---

## 13. Documentación relacionada

| Documento | Contenido |
|-----------|-----------|
| [README.md](../README.md) | Arranque rápido y overview |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Flujo y módulos |
| [API.md](./API.md) | Contratos de la API |
| [PRODUCT_SPEC.md](./PRODUCT_SPEC.md) | Resumen del brief de producto |
| `Proyect_Letter/...pdf` | Spec original completa |
