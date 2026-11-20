# AI Underwriting Copilot for MSME Lending

An intelligent, verifiable underwriting copilot that processes MSME loan applicant documents (bank statements, invoices, GST returns), extracts structured data with confidence scores, computes financial risk metrics using deterministic code, retrieves lending policies via hybrid RAG, and drafts credit memos where every claim cites a computed metric ID or policy clause.

## Non-Negotiable Core Principles
1. **The LLM never does math:** All debt ratios, averages, balances, and volatilities are calculated by deterministic code.
2. **Synthetic data only:** Synthetic generator guarantees privacy and reproducibility.
3. **Never fabricate results:** All reported benchmarks come directly from reproducible eval harness execution.
4. **Verifiable citations:** Every claim in an underwriting memo must cite a computed metric or ingested policy clause.
5. **Human-in-the-loop review:** Confidence scores gate fields into a reviewer queue before final decision.

## System Architecture
See [docs/architecture.md](file:///c:/Users/ihars/Desktop/Workspace/ai_engineer/docs/architecture.md) for details and Mermaid diagrams.

## Monorepo Layout
```
├── core-service/        # Spring Boot 3 (Java 21) - REST APIs, JPA, Flyway, Deterministic Metrics
├── ai-service/          # FastAPI & LangGraph (Python 3.11+) - Extraction, RAG, Memo Agent
├── data-gen/            # Synthetic applicant & document generators
├── data/
│   ├── policy_raw/      # Public regulatory & internal credit policy documents
│   └── synthetic/       # Generated applicants, statements, invoices
├── evals/               # Evaluation harnesses (Extraction, Retrieval, Memo, Adversarial)
├── docs/                # Architecture, design decisions, eval results, failure analysis
└── ui/                  # Reviewer UI workbench
```

## Quickstart

### Prerequisites
- Docker & Docker Compose
- Java 21 & Maven 3.9+
- Python 3.11+

### Running the System
```bash
# Copy and configure environment variables
cp .env.example .env

# Start all services with Docker Compose
docker compose up -d
```

### Verification
- Core Service Health: `curl http://localhost:8080/health`
- AI Service Health: `curl http://localhost:8000/health`
- Core -> AI Connectivity: `curl http://localhost:8080/api/ai-service/health`

## Evaluation Results
See [docs/eval-results.md](file:///c:/Users/ihars/Desktop/Workspace/ai_engineer/docs/eval-results.md) for actual harness outputs.

## License
MIT
