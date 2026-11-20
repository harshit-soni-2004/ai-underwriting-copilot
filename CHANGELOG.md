# Changelog

All notable changes to the AI Underwriting Copilot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Phase 0: Scaffolding] - 2026-11-20

### Added
- Monorepo directory structure established.
- Docker Compose configuration with PostgreSQL 16 (`pgvector`), Langfuse v2, `core-service`, and `ai-service`.
- Environment variable configuration via `.env.example` and committed `.env` template.
- Core Service scaffolded with Spring Boot 3.3, Java 21, Spring Data JPA, Flyway baseline migration, and RestClient.
- Flyway V1 migration enabling `vector` extension and defining baseline relational schema.
- AI Service scaffolded with FastAPI, Pydantic v2, and LangGraph structure.
- Health checks for both services and inter-service communication endpoint (`/api/ai-service/health`).
- Sample internal credit policy document in `data/policy_raw/sample_internal_credit_policy.md`.
- Comprehensive documentation: `architecture.md`, `decisions.md`, `eval-results.md`, and `failure-analysis.md`.
- GitHub Actions CI workflow for automated testing.
