# Reference Coverage Audit

The PDF and 12 supplemental images were treated as reference-only material. “Exact” below means every visible line was transcribed or semantically preserved; “adapted” means the screenshot exposed an interface or partial file but not a complete authoritative source.

| PDF page / new image | Visible source | Coverage |
|---|---|---|
| PDF 1 | Repository tree, workflow fragment | Adapted: complete tree recreated; workflow uses safe placeholders because organization actions/secrets were cropped |
| PDF 2 + `initalizer.jpeg` + 4.06.52 | `agent/rag/initializer.py` 1-68 | Exact structure and lifecycle behavior preserved; imports routed through provider adapter |
| PDF 3 | `agent/rag/prompt.py` 1-16 | Exact visible prompt intent preserved and parameterized |
| PDF 4 | `agent/rag/settings.py` 1-39 | Exact dataclass/DSN/env shape preserved |
| PDF 5-6 + 4.06.53 | `agent/rag/tools.py` 1-134 | Full visible control flow preserved; normalized to current context-engine adapter API |
| PDF 7 | `agent/agent_config.py` | Exact visible dataclass fields preserved |
| PDF 8 + 4.06.54 | `agent/checkpointing.py` 1-51 | Exact visible backend selection behavior preserved |
| PDF 9 | `agent/factory.py` | Exact delegation behavior preserved |
| PDF 10-12 + 4.06.57/58/59 | `agent/graph.py` 1-117 | Exact visible graph topology preserved; model import routed through adapter |
| PDF 13 + 4.07.02 | `agent/initialize.py` 1-54 | Exact initialization order and cleanup preserved |
| PDF 14-15 + 4.07.05/06/07 | `agent/main.py` 1-106 | Visible endpoints and graph invocation preserved; expanded to compatible `/api/v1` contracts and safe errors |
| PDF 16-17 + 4.07.08 | `agent/middleware.py` 1-71 | Logging/timing semantics preserved; framework-independent wrapper added for compatibility |
| PDF 18 | `config/constants.py` | Visible constants preserved; required plan variables added |
| PDF 19-21 | `config/env.py` | Exact precedence semantics preserved; parser adapted for local availability |
| PDF 22 | `config/prompts.py` | Visible prompt assembly preserved |
| PDF 23 | `config/settings.py` | Visible immutable settings lifecycle preserved |
| PDF 24 | Langfuse skill | Adapted: screenshot was incomplete; visible variables and safety requirements preserved |
| PDF 25-26 | RAG skill | Adapted: visible configuration variables, defaults, validation and verification preserved |
| PDF 27 | Remote DAG skill | Adapted: visible API/auth/timeout contract preserved; provider implementation intentionally left optional |
| PDF 28 | `scripts/install.sh` | Adapted: architecture and Python detection preserved without proprietary package-index URLs |
| PDF 29 | `scripts/start_docker.sh` | Adapted: visible EPAS/local split preserved |
| PDF 30 | `scripts/start_local.sh` | Adapted: visible env, venv and Uvicorn flow preserved |

## Unavoidable adaptations

- Proprietary `amex-genai`, `safechain`, and `aix_context_engine` packages are loaded when installed; deterministic local adapters allow tests without enterprise infrastructure.
- Proprietary registry actions, credentials, chart conventions, and incomplete YAML were replaced with explicit placeholders and standard Kubernetes resources.
- The screenshot’s `/chat` contract was expanded to the requested Auxiliator `/api/v1` contract while retaining LangGraph `thread_id` behavior.

## Unresolved reference regions

- No complete screenshot source was supplied for SafeChain YAML, Helm subcharts, Dockerfile, Gunicorn config, Makefile, `pyproject.toml`, or GitHub organization actions.
- These files are therefore documented adaptations and are not claimed to be byte-for-byte copies.
