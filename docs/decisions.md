# Architectural Decisions Log

This log records notable design choices, alternatives considered, and trade-offs made across the phases.

## 001 - Dual-Service Architecture: Spring Boot Core + Python AI Service
- **Date**: Phase 0
- **Context**: Need a robust, enterprise-grade underwriting backend with ACID transactions, audit logging, idempotent decision workflows, and seamless LangGraph orchestration for complex agentic flows.
- **Decision**: Split the system into:
  1. `core-service`: Java 21 & Spring Boot 3 handling database persistence, Flyway migrations, authentication, deterministic metric calculations, audit records, and state transitions.
  2. `ai-service`: Python 3.11+ with FastAPI, Pydantic v2, and LangGraph for OCR extraction, RAG policy retrieval, prompt guardrails, and credit memo drafting.
- **Alternatives Considered**:
  - *Single Python service*: Fast to prototype, but weaker enterprise transaction/concurrency primitives, audit tooling, and type-safe financial computation rigor compared to Spring Boot 3.
  - *Single Java service (LangChain4j)*: Emerging, but Python ecosystem offers substantially superior document parsing, vision models, LangGraph state machines, and evaluation frameworks.
- **Trade-off**: Requires running two runtimes and maintaining API contracts between them, offset by Docker Compose automation and typed schemas.

## 002 - Unified Postgres + pgvector Storage
- **Date**: Phase 0
- **Context**: Need relational persistence for applicants, documents, decisions, and audit trails alongside vector search for policy retrieval.
- **Decision**: Standardize on PostgreSQL 16 with `pgvector`.
- **Alternatives Considered**:
  - *Dedicated vector DB (Pinecone, Qdrant)*: Extra infrastructure dependency, separate backup cycles, and cross-database transaction complexities.
- **Trade-off**: Relational and vector data reside in a single database instance, simplifying backups, local development, and transactional integrity.

## 003 - Pure Deterministic Code for Financial Calculations
- **Date**: Phase 0
- **Context**: LLMs are notoriously prone to floating-point errors, hallucinated totals, and subtle math distortions.
- **Decision**: Rule 1 strictly enforces that financial metrics are computed entirely in pure Java code with comprehensive unit test coverage and edge cases. The LLM only receives and cites verified metrics.
- **Trade-off**: Zero hallucinated numbers in credit decisions, with auditable financial math.
