# System Architecture: AI Underwriting Copilot for MSME Lending

```mermaid
flowchart TD
    subgraph UI ["Reviewer UI (Angular / React)"]
        UI_Dash["Applicant Review & Memo Workbench"]
    end

    subgraph CoreService ["Core Service (Java 21 / Spring Boot 3)"]
        REST_API["REST Controllers"]
        SEC["Spring Security (JWT)"]
        FLYWAY["Flyway Migrations"]
        AUDIT["Audit & Idempotent Decision Engine"]
        DET_METRICS["Deterministic Metrics Engine"]
        REST_API --> DET_METRICS
        REST_API --> AUDIT
    end

    subgraph AIService ["AI Service (Python 3.11+ / FastAPI & LangGraph)"]
        FAST_API["FastAPI App (/health, /extract, /memo)"]
        EXTRACT["Extraction Pipeline (OCR / Vision LLM)"]
        RETRIEVAL["Hybrid RAG (BM25 + Vector + Rerank)"]
        GUARD["Prompt Injection Defense & Guardrails"]
        AGENT["LangGraph Underwriting Agent"]
        FAST_API --> GUARD
        GUARD --> AGENT
        AGENT --> EXTRACT
        AGENT --> RETRIEVAL
    end

    subgraph Storage ["PostgreSQL 16 + pgvector"]
        DB_APP["Structured Tables: Applicants, Extractions, Decisions"]
        DB_VEC["Vector Storage: Policy Embeddings"]
    end

    subgraph Observability ["Observability"]
        LANGFUSE["Langfuse (Traces, Cost, Latency)"]
    end

    UI_Dash --> REST_API
    REST_API <--> FAST_API
    REST_API --> DB_APP
    AIService --> DB_VEC
    AIService --> LANGFUSE
```

## Architectural Design Principles

1. **Deterministic Metrics vs Generative Synthesis**:
   - The LLM never computes arithmetic, interest, debt ratios, or financial aggregates.
   - Core-Service computes verified metrics (DSCR, AMB, Inflow/Outflow volatility, Cheque Bounce rates) in deterministic, test-driven Java code.
   - The AI Service cites these verified figures by metric ID.

2. **Confidence-Gated Review Pipeline**:
   - Every extracted field carries a confidence score [0.0, 1.0] and source provenance.
   - Low confidence fields (< 0.85 default threshold) are marked `NEEDS_REVIEW` and routed to the human reviewer queue.

3. **Citations as Invariants**:
   - Credit memos must explicitly ground every claim against a verified metric ID or an ingested policy clause ID.
   - Uncited claims trigger validation rejection in the agent graph.

4. **Multi-Model / Swappable Providers**:
   - LLMs and embeddings are accessed via unified abstractions swappable via `.env` (Gemini, OpenAI, Anthropic, Ollama).
