# Salesforce Playbook Agent

An AIX/LangGraph assistant that recommends seller-reviewed next-best-action playbooks for
Salesforce opportunities using approved playbooks and historical win/loss patterns.

The repository ships with synthetic SME-review templates only. Replace or validate these
templates with governed Salesforce history before production use.

## Governed Intelligence POC

Phase 3 adds a bounded governed runtime, an official MCP v2 Skill Gateway at `/mcp/`, registry-constrained Draft generation, strict role-gated lifecycle transitions, a React Skill Studio, and a unified Skills/Signals/Capabilities/Policies Catalog. Generated definitions always remain Drafts; Reviewer approval and Admin publishing are separate operations.

See `docs/intelligence-agent/phase-3-report.md` for the test results and current limitations.

Phase 4 adds synthetic golden evaluations and mandatory publish gates, an auditable human Review Queue, immutable published Skill snapshots with rollback-as-a-new-version, and replayable decision/trace/version Audit views. See `docs/intelligence-agent/phase-4-report.md`.

Phase 5 adds replaceable enterprise adapters, bounded reliability and idempotency controls, event/batch invocation, Observability and sanitized Settings screens, and combined backend/frontend deployment gates. See `docs/intelligence-agent/architecture.md` and `docs/intelligence-agent/runbook.md`.

## Architecture

### Layered enterprise view

The platform provides one governed reasoning layer. Each business use case is expressed as a
versioned Skill configuration; orchestration, evidence validation, confidence, policy, review,
and audit remain shared platform guarantees.

```mermaid
flowchart TB
    Outcome["Transform governed enterprise knowledge into context-aware insights,<br/>recommendations, and reviewable business decisions"]

    subgraph L1["LAYER 1 — EXPERIENCE AND ACTIVATION"]
        direction LR
        Hub["Intelligence Hub<br/>Playground · Decisions · Reviews"]
        NBA["Decisioning<br/>Next Best Action"]
        Ranking["Risk and priority<br/>ranking"]
        Summary["Grounded summaries<br/>and explanations"]
        Quality["Policy-aware<br/>quality checks"]
        Copilot["Salesforce playbook<br/>copilot"]
        APIChannels["API · event · scheduled<br/>and batch channels"]
    end

    subgraph L2["LAYER 2 — GOVERNED CATALOG · CONFIGURATION, NOT PIPELINE CODE"]
        direction LR
        SkillRegistry["SKILL REGISTRY<br/>what to reason"]
        CapabilityRegistry["CAPABILITY REGISTRY<br/>what may be called"]
        SignalRegistry["SIGNAL REGISTRY<br/>what is already known"]
        PolicyRegistry["POLICY PACKS<br/>when to trust or review"]
        VersionRegistry["VERSION + EVALUATION<br/>what may be published"]
    end

    subgraph L3["LAYER 3 — AGENTIC REASONING AND DECISIONING RUNTIME"]
        direction TB
        Orchestrator["LANGGRAPH ORCHESTRATOR<br/>bounded planning · routing · stage control · safe trace"]

        subgraph RuntimeServices["Shared runtime services"]
            direction LR
            Intent["1 · INTENT<br/>deterministic route"]
            Plan["2 · PLAN<br/>bounded execution"]
            Context["3 · CONTEXT<br/>scope · time · provenance"]
            Validate["4 · VALIDATE<br/>sufficiency · recover once"]
            Execute["5 · EXECUTE<br/>one registered Skill"]
            Reason["6 · REASON<br/>rules · analytics · grounded · hybrid"]
            Evidence["7 · EVIDENCE<br/>validate every reference"]
            Confidence["8 · CONFIDENCE<br/>independent scoring"]
            Policy["9 · POLICY<br/>allow · review · reject · abstain"]
            Decide["10 · DECIDE<br/>synthesize and activate"]
            Audit["11 · AUDIT<br/>persist · replay · observe"]

            Intent --> Plan --> Context --> Validate --> Execute --> Reason
            Reason --> Evidence --> Confidence --> Policy --> Decide --> Audit
        end

        Replan["RECOVERY LOOP · widen the time window once<br/>never loops forever · never lowers evidence requirements"]
        Outcomes["ALLOW — automated POC decision  ·  REVIEW — human in the loop<br/>REJECT — policy violation  ·  ABSTAIN — insufficient evidence"]

        Orchestrator --> Intent
        Validate -. "RECOVERABLE" .-> Replan
        Replan -. "max 1" .-> Context
        Policy --> Outcomes
    end

    subgraph L4["LAYER 4 — ENTERPRISE SERVICES AND CONTROL BOUNDARIES"]
        direction LR
        Auth["Identity + authorization<br/>least-privilege roles"]
        MCP["MCP Skill Gateway<br/>typed discovery and execution"]
        Model["Model Gateway<br/>one bounded call + safe fallback"]
        Reliability["Reliability<br/>timeout · retry · circuit breaker"]
        Idempotency["Idempotency<br/>replay identical · reject conflict"]
        Enterprise["Replaceable adapters<br/>Salesforce · Knowledge Fabric · audit · secrets"]
        Operations["Operations<br/>latency · calls · tokens · cost · outcomes"]
    end

    subgraph L5["LAYER 5 — KNOWLEDGE FABRIC AND GOVERNED STATE"]
        direction LR
        Entities["ENTITIES + RELATIONSHIPS<br/>customer · account · opportunity · interaction"]
        Facts["FACTS + METRICS<br/>typed business context"]
        Signals["SIGNALS<br/>confidence · freshness · provenance"]
        Search["SEMANTIC SEARCH<br/>approved playbooks and history"]
        EvidenceStore["EVIDENCE<br/>cited source excerpts"]
        Vector[("POSTGRESQL + PGVECTOR<br/>chunks · metadata · embeddings")]
        GovernanceStore[("GOVERNANCE STORE<br/>decisions · traces · versions · reviews")]
    end

    subgraph Principles["PLATFORM GUARANTEES"]
        direction LR
        P1["Context aware<br/>explicit entity and time scope"]
        P2["Bounded reasoning<br/>14 stages · 1 Skill · 1 model call"]
        P3["Trust by design<br/>evidence · confidence · policy"]
        P4["Human oversight<br/>review · evaluation · rollback"]
        P5["No black box<br/>safe trace · no chain-of-thought"]
    end

    Outcome --> L1
    L1 -->|"request with identity, scope and intent"| L2
    L2 -->|"registries are read throughout execution"| L3
    L3 -->|"typed tool and provider calls"| L4
    L4 -->|"one governed access layer"| L5
    L5 -->|"facts · signals · semantic context · evidence"| L3
    L3 -->|"decision · confidence · evidence · policy · trace"| L1
    L5 --> Principles

    classDef title fill:#17345f,color:#ffffff,stroke:#17345f,stroke-width:2px;
    classDef catalog fill:#edf4ff,color:#17345f,stroke:#4776b4,stroke-width:1.5px;
    classDef runtime fill:#fff8e6,color:#4a3814,stroke:#b08a3e,stroke-width:1.5px;
    classDef active fill:#2367ad,color:#ffffff,stroke:#184c82,stroke-width:2px;
    classDef service fill:#f2ecff,color:#3c2d64,stroke:#7964a8,stroke-width:1.5px;
    classDef data fill:#132c50,color:#ffffff,stroke:#132c50,stroke-width:1.5px;
    classDef guarantee fill:#e8f6ef,color:#164c35,stroke:#398260,stroke-width:1.5px;

    class Outcome title;
    class SkillRegistry,CapabilityRegistry,SignalRegistry,PolicyRegistry,VersionRegistry catalog;
    class Orchestrator,Intent,Plan,Context,Validate,Execute,Evidence,Confidence,Policy,Decide,Audit,Replan,Outcomes runtime;
    class Reason active;
    class Auth,MCP,Model,Reliability,Idempotency,Enterprise,Operations service;
    class Entities,Facts,Signals,Search,EvidenceStore,Vector,GovernanceStore data;
    class P1,P2,P3,P4,P5 guarantee;
```

The layer boundaries are deliberate: experience channels consume decisions, the catalog declares
each use case, the shared runtime owns reasoning and governance, enterprise ports isolate provider
dependencies, and the Knowledge Fabric supplies typed context and evidence.

### Detailed component and execution view

```mermaid
flowchart TB
    %% Entry channels
    subgraph Channels["Invocation channels"]
        User["Business user"]
        Hub["React + TypeScript<br/>Intelligence Hub"]
        ApiClient["REST API client"]
        EventSource["Synthetic event source"]
        BatchSource["Scheduled / batch source"]
        McpConsumer["External MCP consumer"]

        User --> Hub
        ApiClient --> REST
        EventSource --> EventAPI
        BatchSource --> BatchAPI
    end

    %% FastAPI boundary
    subgraph Application["FastAPI application boundary"]
        Static["Production static UI<br/>/app/"]
        REST["Interactive intelligence API<br/>/api/v1/intelligence/execute"]
        Stream["SSE execution API<br/>/execute/stream"]
        EventAPI["Event invocation<br/>/intelligence/events"]
        BatchAPI["Batch simulation<br/>/simulate-batch"]
        Legacy["Compatible APIs<br/>chat · retrieve · index · playbook"]
        CatalogAPI["Catalog and governance APIs<br/>skills · signals · policies · reviews · evaluations"]
        OpsAPI["Operations APIs<br/>observability · settings · traces · audit"]
        Auth["POC identity and authorization<br/>Viewer · Author · Reviewer · Admin"]
        RequestContext["Request ID · correlation ID<br/>safe structured errors"]

        Hub --> Static
        Hub --> REST
        Hub --> Stream
        Hub --> CatalogAPI
        Hub --> OpsAPI
        REST --> Auth
        Stream --> Auth
        EventAPI --> Auth
        BatchAPI --> Auth
        CatalogAPI --> Auth
        OpsAPI --> Auth
        Auth --> RequestContext
        Legacy --> RequestContext
    end

    %% Reliability controls
    subgraph Reliability["Enterprise reliability control plane"]
        Invocation["Invocation Service"]
        Idempotency["Idempotency store<br/>replay identical · reject conflict"]
        Limits["Bounded execution<br/>14 stages · 1 replan · 1 skill<br/>4 tools · 1 model · 2K tokens · 15 sec"]
        Retry["Classified retry + timeout"]
        Breakers["Circuit breakers<br/>closed · open · half-open"]

        Invocation --> Idempotency
        Invocation --> Limits
        Retry --> Breakers
    end

    RequestContext --> Invocation

    %% Governed LangGraph runtime
    subgraph Runtime["Governed LangGraph runtime"]
        direction LR
        N1["1 Receive"] --> N2["2 Resolve scope"] --> N3["3 Resolve intent"]
        N3 --> N4["4 Select skill"] --> N5["5 Plan"] --> N6["6 Assemble context"]
        N6 --> N7["7 Validate sufficiency"] --> N8["8 Execute skill"]
        N8 --> N9["9 Validate evidence"] --> N10["10 Calculate confidence"]
        N10 --> N11["11 Apply policy"] --> N12["12 Decide"]
        N12 --> N13["13 Activate"] --> N14["14 Audit"]
    end

    Limits --> N1

    %% Context assembly
    subgraph ContextLayer["Context and evidence plane"]
        Scope["Entity scope resolver<br/>customer · account · opportunity · interaction"]
        ContextEngine["Context Engine<br/>time filter · deduplication · provenance · freshness"]
        Sufficiency["Evidence sufficiency<br/>SUFFICIENT · RECOVERABLE · INSUFFICIENT"]
        SyntheticRepo["Synthetic POC repository<br/>entities · facts · relationships · signals · evidence"]
        Knowledge["Knowledge base<br/>approved Markdown playbooks"]
        PgVector[("PostgreSQL + pgvector<br/>chunks · metadata · embeddings")]

        Scope --> ContextEngine
        SyntheticRepo --> ContextEngine
        Knowledge --> PgVector
        PgVector --> ContextEngine
        ContextEngine --> Sufficiency
    end

    N2 --> Scope
    ContextEngine --> N6
    Sufficiency --> N7

    %% Skills and reasoning
    subgraph SkillPlane["Reusable Skill execution plane"]
        Router["Deterministic intent router<br/>clarifies ambiguity without an LLM"]
        Registry["YAML Skill Registry<br/>definitions · schemas · lifecycle · versions"]
        MCPClient["In-memory MCP client boundary"]
        MCPServer["Official Python MCP v2 Skill Gateway<br/>list · get · schema · execute"]
        Strategy["Strategy router"]
        Rules["Deterministic rules<br/>Engagement Decline"]
        Analytics["Analytics<br/>Rewards Orientation"]
        Grounded["Grounded LLM<br/>Complaint Root Cause"]
        Hybrid["Rules + grounded explanation<br/>Opportunity Risk"]

        Router --> Registry
        Registry --> MCPClient
        MCPClient --> MCPServer
        MCPServer --> Strategy
        Strategy --> Rules
        Strategy --> Analytics
        Strategy --> Grounded
        Strategy --> Hybrid
    end

    N3 --> Router
    Registry --> N4
    N8 --> MCPClient
    McpConsumer -->|"Bearer token · Streamable HTTP /mcp/"| MCPServer

    %% Governance
    subgraph Governance["Deterministic governance plane"]
        EvidenceValidation["Evidence reference validation<br/>unsupported claims cannot pass silently"]
        Confidence["Independent confidence<br/>coverage 35% · signal 25% · reliability 20%<br/>consistency 10% · freshness 10% · penalties"]
        Policy["Policy engine<br/>ALLOW · REVIEW · REJECT · ABSTAIN"]
        Review["Human Review Queue<br/>approve · reject · modify · comment"]
        Evaluation["Golden-data evaluation<br/>mandatory publish gates"]
        Versions["Immutable Skill snapshots<br/>rollback creates a new version"]
        Audit["Replayable audit record<br/>no chain-of-thought"]

        EvidenceValidation --> Confidence --> Policy
        Policy -->|"REVIEW"| Review
        Evaluation --> Versions
        Review --> Audit
        Versions --> Audit
    end

    N9 --> EvidenceValidation
    Confidence --> N10
    Policy --> N11
    N14 --> Audit

    %% Persistence and operations
    subgraph Persistence["Persistence and operations"]
        GovRepository["Governance Repository interface"]
        Memory[("In-memory POC store")]
        Postgres[("PostgreSQL JSONB<br/>decisions · safe traces")]
        Operations["Operational aggregation<br/>latency · retries · calls · tokens · mock cost<br/>versions · outcomes · review state"]
        Observability["Observability workbench"]
        Settings["Sanitized Settings workbench<br/>configuration presence only"]

        GovRepository --> Memory
        GovRepository --> Postgres
        Memory --> Operations
        Postgres --> Operations
        Operations --> Observability
        Operations --> Settings
    end

    N12 --> GovRepository
    N14 --> GovRepository
    Review --> GovRepository
    Audit --> GovRepository
    Observability --> OpsAPI
    Settings --> OpsAPI

    %% Replaceable integrations
    subgraph EnterprisePorts["Replaceable enterprise adapter ports"]
        IdentityPort["Identity / IAM"]
        AuthorizationPort["Authorization"]
        ModelPort["Model gateway"]
        SecretsPort["Secrets provider"]
        AuditPort["Enterprise audit sink"]
        KnowledgePort["Knowledge Fabric"]
        SalesforcePort["Salesforce"]

        ModelAdapter["Safe fallback model adapter"]
        SecretAdapter["Environment secrets adapter"]
        KnowledgeAdapter["Synthetic Knowledge Fabric adapter"]
        SalesforceAdapter["Synthetic Salesforce adapter"]

        ModelPort --> ModelAdapter
        SecretsPort --> SecretAdapter
        KnowledgePort --> KnowledgeAdapter
        SalesforcePort --> SalesforceAdapter
    end

    Auth -. "production replacement" .-> IdentityPort
    Auth -. "production replacement" .-> AuthorizationPort
    Grounded --> Retry
    Hybrid --> Retry
    Retry --> ModelPort
    ContextEngine -.-> KnowledgePort
    Legacy -.-> SalesforcePort
    N14 -.-> AuditPort

    %% Delivery
    subgraph Delivery["Build and deployment"]
        Tests["Quality gates<br/>Ruff · mypy · pytest · ESLint · Vitest · Vite"]
        Docker["Multi-stage Docker image<br/>Node build + Python runtime"]
        Helm["Helm deployment<br/>health probes · env · secretRef"]
        CI["GitHub Actions<br/>test · build · registry placeholder"]

        Tests --> CI
        CI --> Docker
        Docker --> Helm
    end

    classDef control fill:#e8f0fe,stroke:#315da8,color:#102a43;
    classDef governance fill:#fff4d6,stroke:#b7791f,color:#5f370e;
    classDef storage fill:#e6fffa,stroke:#2c7a7b,color:#234e52;
    classDef external fill:#f3e8ff,stroke:#805ad5,color:#44337a;
    class Invocation,Idempotency,Limits,Retry,Breakers,N1,N2,N3,N4,N5,N6,N7,N8,N9,N10,N11,N12,N13,N14 control;
    class EvidenceValidation,Confidence,Policy,Review,Evaluation,Versions,Audit governance;
    class PgVector,Memory,Postgres,GovRepository storage;
    class IdentityPort,AuthorizationPort,ModelPort,SecretsPort,AuditPort,KnowledgePort,SalesforcePort external;
```

### Request lifecycle

1. A user, API, event, or batch trigger enters FastAPI and is authenticated and authorized.
2. The Invocation Service enforces idempotency and the fixed runtime budget.
3. LangGraph resolves scope and intent, selects one registered Skill, and assembles only relevant context.
4. Insufficient evidence causes recovery once or a safe abstention; it never triggers an ungrounded model call.
5. The selected Skill executes through MCP using deterministic rules, analytics, grounded LLM reasoning, or a bounded hybrid strategy.
6. Evidence references are validated, confidence is calculated outside the model, and deterministic policy produces `ALLOW`, `REVIEW`, `REJECT`, or `ABSTAIN`.
7. The decision and safe trace are persisted, exposed to review and audit workflows, and summarized in Observability without storing prompts or chain-of-thought.

### Architectural guarantees

- Skills and models cannot publish themselves or bypass evidence, confidence, authorization, or policy controls.
- Deterministic Skills make zero model calls; grounded and hybrid Skills are limited to one model call.
- Enterprise systems are accessed through narrow adapter interfaces so POC implementations can be replaced without changing runtime contracts.
- Secrets, connection strings, model payloads, prompts, and chain-of-thought are excluded from settings, errors, and traces.
- Every included customer, opportunity, interaction, signal, evaluation result, and demo identity is synthetic.

## Local start

```bash
cp .env.example .env
./scripts/install.sh
./scripts/start_local.sh
```

Open `http://localhost:8080/docs`.

Start the native PostgreSQL 16 installation, then start the application:

```bash
make db-up
./scripts/start_local.sh
```

At startup, every Markdown file under `knowledge/sales/` is chunked, embedded, and idempotently
upserted into PostgreSQL. PostgreSQL with pgvector is the system of record for content, metadata,
and embeddings. The internal SafeChain embedding provider is selected when installed, with a
deterministic local embedding adapter for development.

## Recommend a playbook

```bash
curl -X POST http://127.0.0.1:8080/api/v1/playbook/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "opportunity_name": "Acme Expansion",
    "stage": "Solution Validation",
    "industry": "Financial Services",
    "customer_segment": "Enterprise",
    "deal_value": 250000,
    "days_in_stage": 35,
    "recent_activity": "Only one contact attended the last meeting",
    "pain_points": ["manual onboarding"],
    "competitors": ["Competitor A"]
  }'
```

Recommendations are advisory. Customer messages, pricing, forecasts, contracts, and Salesforce
record changes require human approval.

Database commands are also available through Make:

```bash
make db-up       # start native PostgreSQL/pgvector
make db-status   # check native server readiness
make db-shell    # open psql
make db-down     # stop the database
```

Postgres.app is installed at `~/Applications/Postgres.app`. Docker remains an
optional fallback through `make db-up-docker` and uses host port 5433.

Local connection details come from the ignored `.env` file:

```text
postgresql://auxiliator:auxiliator-local@127.0.0.1:5432/context_engine
```

The application creates the `vector` extension, `public.sales_playbook_chunks` table, primary key,
and department index automatically during startup.

## Verification

```bash
make test
make lint
make typecheck
```

See `docs/reference-coverage.md` for the screenshot/PDF fidelity audit.
