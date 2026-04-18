---
tags:
- project
last_compiled: '2026-04-17'
---
# trust-systems

## Summary
The trust-systems project is a comprehensive enterprise decision-making platform and software supply chain management system that leverages local-first architecture, Docker Compose, and various observability tools like OpenTelemetry, Jaeger, and OPA. It includes components such as the Decision Trace Gateway, Worker Service, Audit Packet, and more, with a focus on authorization, traceability, idempotent execution, and policy enforcement. The system is designed for proof-carrying operations and includes detailed documentation, threat models, and a roadmap for development.

## Dependencies
- Docker Compose
- Kubernetes
- OpenTelemetry
- Jaeger
- TLA+
- GitOps
- Helm charts
- SBOM
- Policy enforcement
- Audit Packet
- Supply chain evidence
- OPA
- Kafka
- Redpanda
- Kind
- k3d
- OTel collector

## Strategic Gap Analysis
The trust-systems project has a strong focus on local-first architecture, observability, and policy enforcement, but there is a need for more comprehensive threat modeling and integration with GitOps, Helm charts, and advanced testing of OPA policies for production environments. Additionally, there is a gap in the documentation for advanced usage, troubleshooting scenarios, and the scalability and performance of the infrastructure setup, especially in production environments.
