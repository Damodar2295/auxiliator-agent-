# Intelligence Agent Repository Assessment

## Assessment status

This assessment was completed before Intelligence Agent implementation. The repository at
`poc/auxiliator-agent` is the authoritative implementation target. The name `auxiliator-agent-a`
in the source brief is treated as descriptive rather than a request to rename the repository.

## 1. Existing architecture summary

The project is a Python 3.11+ FastAPI service. Application startup is managed through a FastAPI
lifespan that loads environment configuration, initializes embedding and document-store adapters,
seeds Markdown knowledge, and compiles a LangGraph graph. The graph is a supervisor/tool loop with
LangGraph checkpointing. PostgreSQL/pgvector is the persistent knowledge store; deterministic
in-memory adapters support tests. Docker, Gunicorn, Helm, Make, and GitHub Actions provide basic
delivery scaffolding. There was no frontend before this POC.

## 2. Existing reusable components

- FastAPI application, middleware, health endpoints, and typed Pydantic requests/responses.
- FastAPI lifespan and centralized environment precedence.
- `GraphFactory` and LangGraph compilation boundary.
- Memory/PostgreSQL checkpointer selection.
- Enterprise model loader with local deterministic fallback.
- PostgreSQL/pgvector and in-memory document-store adapters.
- RAG settings, initialization, asynchronous retrieval tool, and Markdown ingestion.
- Pytest, Ruff, and mypy configuration.
- Docker, Gunicorn, Helm, local scripts, and CI placeholders.

## 3. Existing agent/runtime pattern

`GraphFactory.create()` delegates to `agent.graph.build()`. The graph prepends a system prompt,
invokes a middleware-wrapped chat model, conditionally runs LangChain tools, and checkpoints by
thread ID. Existing chat and Salesforce playbook endpoints call the graph after retrieval. The
runtime is suitable as a construction and lifecycle boundary, but it lacks typed governed stages,
explicit bounds, skill selection, evidence validation, confidence, and policy decisions.

## 4. Existing model integration pattern

`agent.model.amodel()` first attempts the approved enterprise SafeChain provider, then configured
OpenAI or Gemini providers, and finally a deterministic local model. `MiddlewareWrappedLLM`
preserves the model interface. The Intelligence Agent must reuse this gateway and must not add a
second model abstraction. Deterministic routing, authorization, policy, and scoring will not call
the model.

## 5. Existing API pattern

Routes are currently declared in `agent/main.py` with Pydantic models, controlled HTTP errors,
request IDs, response timing, and permissive development CORS. Existing versioned APIs cover
health, indexing, retrieval, chat, and Salesforce playbook recommendations. New APIs should use
routers while preserving those contracts.

## 6. Existing persistence pattern

The application uses `psycopg` directly through a narrow provider adapter. PostgreSQL schema and
pgvector tables are initialized idempotently. Unit tests select in-memory storage. Governance
storage should follow the same adapter pattern: memory by default, PostgreSQL optionally, without
introducing a separate ORM.

## 7. Existing UI conventions

No frontend framework, component library, asset pipeline, or UI test convention existed. Phase 1
therefore adds a contained React/TypeScript/Vite application under `frontend/`, using semantic HTML
and a small local design system rather than introducing a large component dependency.

## 8. Existing observability/logging pattern

Python logging records model entry/exit and timing at debug level. HTTP responses include request
ID and elapsed time. There is optional Langfuse packaging but no configured execution tracing,
stage metrics, audit persistence, or UI. These are extension points for later phases.

## 9. Existing MCP/tool support

The graph binds a LangChain asynchronous RAG tool. No MCP SDK, MCP server, discovery gateway, or MCP
client exists. Phase 3 will add one MCP-facing Skill Gateway backed by the same Skill Registry;
Phase 1 does not create a parallel tool system.

## 10. Existing test strategy

Pytest and pytest-asyncio cover health, indexing, retrieval, chat, playbook recommendation,
environment precedence, checkpoint selection, filtering, and partial retrieval failure. Tests use
in-memory adapters and mark live infrastructure tests separately. Frontend tests and Intelligence
Agent contract/registry/auth/routing tests are added in Phase 1.

## 11. Gaps against the Intelligence Agent POC

- No typed intelligence-domain contracts or bounded orchestration state.
- No Signal, Skill, Capability, or Policy registries.
- No realistic pre-derived semantic signal/evidence dataset.
- No deterministic intent router or explicit entity/time scope.
- No context, sufficiency, strategy, evidence, confidence, or policy engines.
- No governance repository, review queue, evaluation gate, decision replay, or version workflow.
- No authorization abstraction or role enforcement.
- No MCP gateway.
- No frontend, execution trace view, catalog, or governance workbench.
- Existing Salesforce playbook behavior is domain-specific and not yet represented as a reusable
  governed Skill.

## 12. Recommended implementation mapping

| Existing boilerplate pattern | Intelligence Agent requirement | Action | Reason |
|---|---|---|---|
| FastAPI app and lifespan | Intelligence APIs and runtime startup | Extend | Preserves application lifecycle and health behavior |
| Pydantic API models | Sixteen domain contracts | Reuse | Existing validation convention is sufficient |
| `GraphFactory` and `agent.graph` | Bounded governed orchestration | Extend | Avoids a second orchestration framework |
| Model `amodel()` adapter | Grounded LLM skills and draft generation | Reuse | Keeps enterprise/local provider behavior consistent |
| LangChain tool | Skill invocation | Extend | Phase 3 adds MCP behind the same registry |
| `psycopg` provider | Governance persistence | Extend | Supports memory/PostgreSQL parity without an ORM |
| RAG document store | Optional knowledge evidence | Reuse | Relevant only when semantic document retrieval is justified |
| Python logging middleware | Execution trace and stage metrics | Extend | Keeps safe telemetry centralized |
| Environment precedence | Intelligence limits, auth, and storage config | Reuse | Existing precedence meets enterprise deployment expectations |
| Existing API routes | Backward compatibility | Reuse | Existing clients must continue working |
| No frontend | Intelligence Hub | New | UI is required and no existing convention can be extended |
| No MCP support | Local Skill Gateway | New | Required discovery/invocation boundary, introduced only once |
| Pytest/Ruff/mypy | Backend quality gates | Reuse | Existing tooling already enforces project conventions |
| No frontend test tooling | React quality gates | New | Required for reliable UI behavior |

## Architectural conflicts and resolutions

1. The source brief says not to create another frontend, but this repository has none. A single
   React frontend is therefore necessary rather than duplicative.
2. The existing graph file carries a generated warning, but no assembler exists in the repository.
   The construction boundary is preserved; Intelligence orchestration is added in dedicated
   modules and connected through the existing graph/factory rather than creating a second runtime.
3. The current application performs embeddings and knowledge ingestion, while the new POC begins
   after semantic signal derivation. Existing RAG APIs remain for compatibility, but synthetic
   signals enter the Intelligence layer directly and are never generated by Skills.
4. The existing Salesforce project is narrower than the four requested demonstration Skills.
   Salesforce Opportunity Risk remains one Skill while complaint, rewards, and deterministic
   engagement Skills demonstrate cross-domain reuse.

## Proposed dependencies

- `PyYAML`: loads declarative Skill definitions while Pydantic remains the validation authority.
- `mcp` v2: official MCP discovery/invocation implementation, added in Phase 3.
- React, React DOM, TypeScript, and Vite: required frontend runtime/build foundation.
- Vitest and Testing Library: frontend unit and interaction tests.

No additional database, message broker, workflow engine, model gateway, or UI component library is
required for the POC.

## Risks and trade-offs

- Synthetic data proves architecture, not production accuracy or business impact.
- In-memory governance state is convenient but not durable; PostgreSQL mode is required for replay
  across restarts.
- Deterministic token routing is explainable but needs evaluation and curation as the Skill catalog
  grows.
- Mock authentication demonstrates authorization boundaries but is not production IAM.
- Local model fallback supports demos but does not validate production model quality.
- Adding a frontend expands build/deployment responsibilities; serving its static build through
  FastAPI keeps the production topology simple.
