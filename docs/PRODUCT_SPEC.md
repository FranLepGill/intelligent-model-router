# Product specification (resumen)

Fuente completa: `Proyect_Letter/Intelligent AI Model Routing Platform.pdf`

## Problema

Enviar todas las consultas al mismo modelo genera costo alto, latencia innecesaria, dependencia de un solo vendor y poca trazabilidad de calidad.

## Solución

Plataforma intermediaria (inference gateway) que elige automáticamente el modelo más económico capaz de cumplir calidad, latencia, privacidad y presupuesto.

## Usuarios

1. **Aplicación cliente** — consume la API (atención al cliente, docs, HR, etc.)
2. **Administrador** — configura providers, modelos, límites, políticas
3. **Analista** — consulta métricas, errores, comparaciones

## Demo objetivo

Clasificación de consultas de atención al cliente en:

`password_problem` · `duplicate_charge` · `refund_problem` · `account_blocked` · `general_question`

Con un modelo económico, uno potente, fallback, failover y comparación de costos.

## Estado de implementación

Ver [STATUS.md](./STATUS.md) para el detalle de lo ya construido vs. pendientes del brief.
