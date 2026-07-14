# API — referencia actual (v1)

Base URL local: `http://localhost:8000`

Autenticación: header `X-API-Key`  
Demo: `imr_demo_key_change_me_in_production_abc123`

Interactive docs: `/docs`

---

## Health

### `GET /api/v1/health`

Sin auth.

```json
{ "status": "ok" }
```

---

## Inference

### `POST /api/v1/inference`

Headers opcionales:

- `Idempotency-Key: <string>`

Body:

```json
{
  "task_type": "customer_support",
  "input": "Me cobraron dos veces la factura 18392.",
  "language": "es",
  "priority": "normal",
  "max_cost_usd": 0.05,
  "max_latency_ms": 5000,
  "minimum_quality": 0.85,
  "contains_sensitive_data": false,
  "output_format": "json"
}
```

Campos:

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `task_type` | string | sí | Ej. `customer_support` |
| `input` | string | sí | Texto de la consulta |
| `language` | string | no | Default `es` |
| `priority` | `low\|normal\|high` | no | Default `normal` |
| `max_cost_usd` | float | no | Tope de costo |
| `max_latency_ms` | int | no | Tope de latencia |
| `minimum_quality` | float 0–1 | no | Calidad mínima |
| `contains_sensitive_data` | bool | no | Filtra modelos no autorizados |
| `output_format` | `json\|text` | no | Default `json` |

Respuesta exitosa (ejemplo):

```json
{
  "request_id": "req_abc123def456",
  "status": "completed",
  "output": {
    "category": "duplicate_charge",
    "priority": "high",
    "suggested_response": "Revisaremos el cobro duplicado y te confirmaremos el resultado.",
    "model_note": "provider-a"
  },
  "routing": {
    "selected_model": "model-small",
    "provider": "provider-a",
    "attempts": 1,
    "fallback_used": false,
    "reason": {
      "strategy": "default_model",
      "required_quality": 0.85,
      "expected_quality": 0.88,
      "estimated_cost": 0.00001234,
      "estimated_latency_ms": 650,
      "discarded_models": {}
    }
  },
  "usage": {
    "input_tokens": 12,
    "output_tokens": 20,
    "latency_ms": 130,
    "estimated_cost_usd": 0.000016
  },
  "error": null
}
```

### `GET /api/v1/requests/{request_id}`

Devuelve el mismo shape que inference.

### `GET /api/v1/requests?limit=50`

Lista resumida del historial del cliente autenticado.

---

## Models

### `GET /api/v1/models`

Lista modelos registrados.

### `POST /api/v1/models`

Registra un modelo nuevo. Si `is_default=true`, desmarca el default anterior.

### `PATCH /api/v1/models/{model_id}`

Actualización parcial (enabled, costos, calidad, etc.).

---

## Errores comunes

| HTTP | Motivo |
|------|--------|
| 401 | API key ausente / inválida / revocada / expirada |
| 403 | Cliente no activo |
| 404 | Request o model no encontrado |
| 409 | Model id duplicado |
| 413 | Input demasiado grande |
| 422 | Validación Pydantic |
| 502 | Adapter de provider no registrado |

---

## Evaluations (Fase 5)

### `GET /api/v1/evaluations/datasets`

Lista datasets disponibles (demo: `customer-support-v1` con 80 casos).

### `GET /api/v1/evaluations/datasets/{dataset_id}`

Detalle del dataset + casos.

### `POST /api/v1/evaluations/run`

Ejecuta todos los casos contra los modelos indicados (o todos los enabled).

```json
{
  "dataset_id": "customer-support-v1",
  "model_ids": ["model-small", "model-medium"],
  "update_model_quality": true
}
```

Actualiza `quality_by_task` de cada modelo con el score medido (blend 30% histórico / 70% nueva eval) para que el router use datos reales de evaluación.

### `GET /api/v1/evaluations/{evaluation_id}`

Resumen de la corrida (accuracy, costo, latencia, calidad por dificultad/idioma).

### `GET /api/v1/evaluations/{evaluation_id}/results`

Resultados por caso/modelo.

### `GET /api/v1/evaluations`

Historial de corridas.

## Endpoints del brief aún no expuestos

- `POST /api/v1/routing-policies`
