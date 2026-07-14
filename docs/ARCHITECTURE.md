# Arquitectura — estado actual

## Visión

Monolito modular: una sola aplicación FastAPI con módulos internos desacoplados. El routing no conoce detalles HTTP de cada vendor; solo habla con `ProviderAdapter`.

```text
Aplicacion cliente
       |
       v
 FastAPI /api/v1
       |
       v
 Authentication   (X-API-Key -> hash -> Client activo)
       |
       v
 Feature extract  (tokens, longitud, complejidad, sensible)
       |
       v
 Routing engine   (filter -> score -> explicacion)
       |
       v
 Provider adapter (provider-a / provider-b — mocks hoy)
       |
       v
 Response validator (JSON + campos requeridos)
       |
  ok --+-- no --> siguiente modelo (fallback)
       |
      yes
       |
       v
 Persistencia PostgreSQL (request + attempts + usage)
       |
       v
 Respuesta al cliente
```

## Módulos

| Módulo | Responsabilidad | Estado |
|--------|-----------------|--------|
| `authentication` | Generar/hashear/validar API keys | Activo |
| `providers` | Interfaz + registry + mocks | Activo (mocks) |
| `routing` | Features + filtro + score | Activo |
| `inference` | Orquestación del flujo | Activo |
| `validation` | Validar output estructurado | Activo |
| `evaluations` | Datasets / métricas | Stub |
| `billing` | Agregación de costos | Stub |
| `observability` | Métricas / traces | Stub |
| `audit` | Auditoría sensible | Stub |

## Flujo de un request de inferencia

1. Validar body (`InferenceRequestCreate`).
2. Autenticar API key y cliente activo.
3. Si hay `Idempotency-Key` y existe resultado previo, devolverlo.
4. Extraer features.
5. Crear `InferenceRequest` (`status=running`).
6. Cargar política del `task_type` y modelos enabled.
7. Loop de intentos (hasta `maximum_attempts`):
   - Intento 1: preferir modelo `is_default`.
   - Siguientes: scoring excluyendo ya usados.
   - Llamar adapter del provider.
   - Si error de provider: registrar attempt failed y continuar si `allow_fallback`.
   - Si respuesta inválida: registrar `invalid_response` y continuar.
   - Si ok: marcar `completed`, guardar output/usage/routing y responder.
8. Si se agotan intentos: `failed` con último error.

## Estrategias de routing

Definidas en `RoutingStrategy`:

- `cheapest` — minimiza costo estimado sujeto a calidad
- `fastest` — minimiza latencia promedio
- `quality_first` — maximiza calidad
- `balanced` — equilibra calidad, costo, latencia y confiabilidad

## Persistencia

- Engine async: `postgresql+asyncpg://…`
- Migraciones: Alembic (`alembic upgrade head` en el arranque Docker)
- Redis está en Compose para fases siguientes (rate limit / cache); la app aún no lo usa de forma activa.

## Extender con un provider real

1. Implementar una clase que herede `ProviderAdapter`.
2. Mapear request común a la API del vendor.
3. Devolver `ProviderResponse` (content, tokens, latency, errores tipados).
4. Registrar en `get_provider_adapter` / registry.
5. Crear fila en `model_providers` + `ai_models`.
6. Poner API keys solo en variables de entorno.
