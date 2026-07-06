# QEDesk Integration Status

This document separates what QEDesk actually wires into the workstation from
what is only a researched or proposed integration.

QEDesk must not imply that a third-party open-source project is implemented
when it is only listed as a candidate.

## Status Legend

| Status | Meaning |
| --- | --- |
| `wired` | Installed and used by a QEDesk command or config path. |
| `wired-prototype` | A real command path exists, but the feature is early and may require user API keys or manual review. |
| `wired-config` | QEDesk ships configuration for the tool, while user auth or the host app lives outside the repo. |
| `wired-via-mathlib` | Available because it is pinned through the Mathlib Lake dependency graph. |
| `installed-only` | Installed in the container, but not yet used by QEDesk commands. |
| `documented-contract` | QEDesk defines a local contract inspired by the tool, but has not integrated the tool itself. |
| `roadmap` | Mentioned as a future integration candidate only. |
| `not-integrated` | Not installed, not configured, and not called. |

## Current Integrations

| Project / Tool | Current Status | Where It Appears | Notes |
| --- | --- | --- | --- |
| Lean 4 / Lake / Elan | `wired` | `Dockerfile`, `lean-toolchain`, `lakefile.lean`, `bin/qedesk`, `bin/lean` | Core verifier and LSP server path. |
| `mathlib4` | `wired` | `lakefile.lean`, `lake-manifest.json`, `src/Proof.lean` | Pinned to the Lean-compatible `v4.31.0` mathlib commit. |
| `Aesop` | `wired-via-mathlib` | `lakefile.lean`, `lake-manifest.json` | Pulled by mathlib and available for optional proof-search experiments. Not imported by the default exercise file because it is heavy. |
| `ProofWidgets4` | `wired-via-mathlib` | `lakefile.lean`, `lake-manifest.json` | Pulled by mathlib and available for future UI/proof-state experiments. Not imported by the default exercise file because it is heavy. |
| `import-graph` | `wired-via-mathlib` | `lakefile.lean` | Pulled by mathlib as `importGraph`; not yet exposed through a QEDesk command. |
| `LeanSearchClient` | `wired-via-mathlib` | `lakefile.lean` | Pulled by mathlib; not yet exposed through a QEDesk command. |
| Docker Compose | `wired` | `docker-compose.yml`, `bin/qedesk`, `bin/qedesk.bat` | Runs the monolithic QEDesk container. |
| LaTeX / latexmk / minted support | `wired` | `Dockerfile`, `bin/qedesk pdf`, `src/main.tex` | Builds the student-facing PDF note. |
| `lean-lsp-mcp` | `wired` | `Dockerfile`, `bin/qedesk agent`, `opencode.json` | Used as the MCP bridge through `./bin/qedesk agent`. |
| OpenCode | `wired-config` | `opencode.json` | QEDesk provides project config; the OpenCode CLI/auth live on the host. |
| OpenRouter | `wired-prototype` | `opencode.json`, `.env.example`, `qedesk-router.json`, `tools/qedesk_router.py`, `bin/qedesk audit`, `bin/qedesk repair`, `bin/qedesk formalize`, `bin/qedesk route`, `bin/qedesk cost` | QEDesk can build compact prompts, route model tiers, call OpenRouter through the OpenAI-compatible API, and log costs. API key/auth is intentionally not stored in the repo. |
| `leanblueprint` | `wired` | `Dockerfile`, `tools/qedesk_sync.py`, `bin/qedesk blueprint` | QEDesk generates `blueprint/src/content.tex` and runs `leanblueprint web` to build HTML and dependency graph output. |
| `leanclient` | `installed-only` | `Dockerfile` | Installed for future direct Lean client experiments; not currently called. |
| `openai` Python package | `wired-prototype` | `Dockerfile`, `tools/qedesk_router.py` | Used by the OpenRouter router prototype. Dry-run mode works without an API key. |
| `sympy` | `installed-only` | `Dockerfile` | Available for future math utilities; not currently called. |
| `plasTeX` | `wired` | `Dockerfile`, `bin/qedesk blueprint`, `blueprint/src/plastex.cfg` | Used by Lean Blueprint's HTML renderer when building the local proof graph. |
| `pylatexenc` | `installed-only` | `Dockerfile` | Installed for lightweight LaTeX text extraction experiments. |
| `jsonschema` | `wired` | `Dockerfile`, `tools/qedesk_sync.py`, `schemas/qedesk-dag.schema.json` | Validates the generated QEDesk DAG sidecar when the package is available. |
| QEDesk DAG sidecar | `wired` | `tools/qedesk_sync.py`, `build/qedesk-dag.json`, `build/qedesk-dag.mmd`, `schemas/qedesk-dag.schema.json` | `qedesk sync` generates JSON and Mermaid sidecars from QEDesk node markers. |
| Lean Blueprint source and web output | `wired` | `tools/qedesk_sync.py`, `blueprint/src/content.tex`, `blueprint/web/` | `qedesk sync` generates the source file; `qedesk blueprint` builds the official Lean Blueprint web output and dependency graph. |
| QEDesk OpenRouter cost ledger | `wired-prototype` | `tools/qedesk_ledger.py`, `build/qedesk-ledger.sqlite`, `bin/qedesk cost` | Real model calls append token and estimated-cost rows. Dry-runs intentionally do not spend or record cost. |

## Roadmap-Only Mentions

These names appear in architecture discussions as possible future integrations.
They are not installed or wired in the current repository.

| Project / Tool | Current Status | Intended Future Role |
| --- | --- | --- |
| `Loogle` | `not-integrated` | Theorem search and hallucination reduction. LeanSearchClient is present via mathlib, but Loogle/local index is not configured. |
| `doc-gen4` / `docgen-action` | `not-integrated` | Generated course and API documentation. |
| `tree-sitter-latex` | `not-integrated` | Possible editor/incremental parsing helper. |
| `verbose-lean4` | `not-integrated` | Optional controlled-natural-language beginner mode. |
| `Waterproof Editor` | `not-integrated` | Future education-oriented UI inspiration or integration candidate. |
| `LeanCopilot` | `not-integrated` | Research-only candidate generation, if used at all. |
| `Duper` | `not-integrated` | Optional proof-producing prover candidate, if bounded carefully. Current upstream main uses Lean 4.30.0, so it is not wired into this Lean 4.31.0 project yet. |

## Implementation Policy

When adding a third-party tool, update this file in the same change.

An integration is not considered real until QEDesk has at least one of:

1. a pinned dependency in `lakefile.lean`, `Dockerfile`, or another package
   manifest;
2. a command in `bin/qedesk` or `bin/qedesk.bat`;
3. a tested path in CI or local verification;
4. documentation showing the exact user command and expected output.

Names in `docs/ARCHITECTURE.md` are design candidates unless this file marks
them as `wired`.
