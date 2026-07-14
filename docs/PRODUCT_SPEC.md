# Product specification summary

This repository implements the **Intelligent AI Model Routing Platform** described in the project brief.

Full product requirements live in the original specification (sections 1–30). This scaffold covers:

- Modular monolith layout
- Data model for clients, API keys, providers, models, policies, requests and attempts
- Common inference API
- Deterministic feature extraction + scoring router
- Mock dual-provider adapters with fallback/escalation hooks
- Seeded demo client for local development

Out of scope for v1 (unchanged from the brief): fine-tuning, full contact-center product, Kubernetes, multi-region HA, ML-based routing, audio/video.
