# QEDesk

QEDesk is a containerized proof desk for undergraduate mathematics: Lean 4 for
formalization, LaTeX for notes, and Python for AI-assisted proof tooling.

Everything runs inside one Ubuntu-based Docker container. Your editor stays on
the host machine, while Lean, Lake, LaTeX, Python packages, and MCP tools share
the same container environment.

The project source directory is bind-mounted into `/workspace`. Lean dependency
artifacts under `.lake` live in a Docker named volume so large Mathlib builds do
not churn through the host filesystem.

## Features

- Lean 4 and Lake pinned through `lean-toolchain`
- `mathlib4` pinned to the Lean-compatible `v4.31.0` commit, with Aesop,
  ProofWidgets, import-graph, and LeanSearchClient available through mathlib's
  dependency graph
- LaTeX with `latexmk`, `minted`, and science/math packages
- Python virtual environment with `openai`, `leanclient`, `lean-lsp-mcp`,
  `leanblueprint`, `plasTeX`, `pylatexenc`, `jsonschema`, and `sympy`
- Host editor wrappers for Linux/WSL/macOS and native Windows
- A small `qedesk` command for the common workstation workflow
- Lean-to-TeX/Blueprint sync for checked Lean declarations
- Budget-aware OpenRouter router prototype with dry-run prompts and a SQLite
  cost ledger
- QEDesk v0.2 proof-audit contracts for gap labels, hint levels, generated
  Lean Blueprint source, and DAG sidecars

## Requirements

- Docker Desktop or Docker Engine with Docker Compose
- WSL, Linux, or macOS for the shell commands below

On Windows, use `bin\qedesk.bat` from PowerShell or run `./bin/qedesk` from WSL.

## Quick Start

```bash
./bin/qedesk start
./bin/qedesk prepare
./bin/qedesk lean
./bin/qedesk pdf
```

The first `qedesk start` builds the Docker image, so it can take several
minutes. Later starts should be much faster.

The first Lean preparation can also take a while because QEDesk has to clone
and/or cache `mathlib4`. This is normal. On Windows, this step is faster when
the repository lives inside the WSL Linux filesystem instead of `/mnt/c/...`.

Keep exercise files lightweight when possible. Imports such as `Mathlib.Tactic`,
`Aesop`, and `ProofWidgets` are available, but they can trigger thousands of
Lean build jobs on first use. Start with narrow imports like
`Mathlib.Data.Real.Basic`, then add heavier tools only when the proof actually
needs them.

If `lean`, `pdf`, `shell`, or `agent` says QEDesk is not running, start the
container first:

```bash
./bin/qedesk start
```

## Commands

```bash
./bin/qedesk start         # Build and start the qedesk container
./bin/qedesk stop          # Stop and remove the container
./bin/qedesk restart       # Restart the container
./bin/qedesk status        # Show container status
./bin/qedesk shell         # Open a shell inside the container
./bin/qedesk files         # Show the main files to edit
./bin/qedesk contracts     # Show QEDesk v0.2 contract files
./bin/qedesk sync          # Sync Lean declarations into TeX, blueprint, and DAG files
./bin/qedesk blueprint     # Build blueprint/web/index.html and the dependency graph
./bin/qedesk serve         # Serve the Blueprint UI at http://localhost:8000/
./bin/qedesk prepare       # Build Lean once before launching MCP/OpenCode
./bin/qedesk cache         # Fetch Mathlib/Lean dependency cache when available
./bin/qedesk lean          # Build the Lean library
./bin/qedesk pdf           # Build build/main.pdf from src/main.tex
./bin/qedesk agent         # Run lean-lsp-mcp inside the container
./bin/qedesk audit         # Audit QEDesk nodes through the OpenRouter router
./bin/qedesk formalize     # Ask for local Lean statements or skeletons
./bin/qedesk repair        # Ask for a repair hint from a Lean error
./bin/qedesk route         # Show the selected model tier for a node
./bin/qedesk cost          # Show the OpenRouter cost ledger summary
./bin/qedesk clean         # Remove generated local build artifacts
./bin/qedesk docker-clean  # Remove the local QEDesk container and image
```

## Daily Workflow

Open the source files in your editor. Do not run them directly in the shell.

```text
src/Proof.lean  # Lean definitions and proofs
src/main.tex    # LaTeX notes
```

Then use QEDesk commands to check or build them:

```bash
./bin/qedesk prepare
./bin/qedesk lean
./bin/qedesk pdf
./bin/qedesk sync
./bin/qedesk blueprint
./bin/qedesk serve
./bin/qedesk audit --dry-run --max-nodes 1 src/main.tex
./bin/qedesk route mem_of_mem_image_preimage
./bin/qedesk cost
```

If you forget where the files are:

```bash
./bin/qedesk files
```

If `qedesk pdf` cannot overwrite `build/main.pdf` because it is open in a PDF
viewer, QEDesk will try `build/main-preview.pdf` as a fallback. Close the viewer
and rerun `./bin/qedesk pdf` when you want the canonical `build/main.pdf`
updated.

`qedesk agent` is different from the other commands: it starts an MCP stdio
server for an AI client. Do not type normal shell commands into it. Use
`./bin/qedesk shell` when you want an interactive terminal inside the container.

GNU Make is still supported as a thin compatibility layer:

```bash
make start
make sync
make blueprint
make serve
make prepare
make build-lean
make pdf
```

## Proof-Audit Workflow

QEDesk is designed around one rule: AI audits and suggests; Lean verifies.

The intended v0.2 loop is:

```text
src/main.tex natural proof
-> local gap audit
-> blueprint/DAG decomposition
-> one Lean target in src/Proof.lean
-> Lean check through ./bin/qedesk lean or MCP
-> repair hint
-> LaTeX note update
```

The default gap labels, hint levels, generated Blueprint source, and DAG
sidecar schema are specified in `docs/DATA_CONTRACTS.md`.

The v0.3 token-saving model-routing policy is specified in
`docs/orchestration.md`. QEDesk now includes a first OpenRouter cascade
prototype in `tools/qedesk_router.py`: it reads QEDesk nodes from `src/main.tex`,
builds compact JSON prompts, routes nodes across Flash/Pro/R1 tiers, and logs
real model calls to `build/qedesk-ledger.sqlite`. Use `--dry-run` before adding
an API key to inspect exactly what would be sent.

To enable real OpenRouter calls, copy `.env.example` to `.env`, fill
`OPENROUTER_API_KEY`, then restart the container:

```bash
cp .env.example .env
./bin/qedesk restart
./bin/qedesk audit src/main.tex
```

The router is intentionally conservative. It produces audits, formalization
skeletons, and repair hints; it does not mark proofs as verified. Lean still
decides that through `./bin/qedesk lean` or MCP.

Actual third-party integration status is tracked in `docs/INTEGRATIONS.md`.
Some tools named in the architecture document are roadmap candidates, not
installed dependencies.

OpenCode agents are configured in `opencode.json`:

```text
@qedesk-tutor     # proof audit and blueprint decomposition
@qedesk-fast      # cheap local Lean exploration
@qedesk-verifier  # strict re-audit and soundness check
```

Before opening OpenCode, start and prepare the container:

```bash
./bin/qedesk start
./bin/qedesk cache
./bin/qedesk prepare
opencode
```

`qedesk cache` is an optional speed-up path for Mathlib build artifacts. If the
cache server is slow or unavailable, skip it and run `./bin/qedesk prepare`;
the first local build can take a long time, but later builds reuse the Docker
volume.

Use prompts like:

```text
@qedesk-tutor
Audit src/main.tex with the QEDesk proof-audit protocol. Do not finish the proof.

@qedesk-fast
Work on the current stable Lean lemma only. Try small tactic families and log failures.

@qedesk-verifier
Re-audit this candidate for statement drift, hidden assumptions, and Lean evidence.
```

## Project Layout

```text
.
|-- Dockerfile
|-- docker-compose.yml
|-- Makefile
|-- README.md
|-- AGENTS.md
|-- opencode.json
|-- qedesk-router.json
|-- docs/
|   |-- ARCHITECTURE.md
|   |-- DATA_CONTRACTS.md
|   |-- INTEGRATIONS.md
|   `-- orchestration.md
|-- schemas/
|   `-- qedesk-dag.schema.json
|-- blueprint/
|   |-- README.md
|   `-- src/
|       |-- content.tex
|       |-- web.tex
|       |-- print.tex
|       `-- plastex.cfg
|-- .env.example
|-- .dockerignore
|-- .gitignore
|-- lean-toolchain
|-- lakefile.lean
|-- lake-manifest.json
|-- bin/
|   |-- qedesk
|   |-- qedesk.bat
|   |-- lean
|   `-- lean.bat
|-- tools/
|   |-- qedesk_blueprint_ui.py
|   |-- qedesk_ledger.py
|   |-- qedesk_router.py
|   `-- qedesk_sync.py
`-- src/
    |-- Proof.lean
    `-- main.tex
```

## Blueprint and DAG

`src/main.tex` is the student-facing source of truth.
`./bin/qedesk sync` reads QEDesk node markers in `src/main.tex`, reads checked
Lean declarations from `src/Proof.lean`, updates the generated Lean map in
`src/main.tex`, writes the Lean Blueprint source at `blueprint/src/content.tex`,
and writes both `build/qedesk-dag.json` and `build/qedesk-dag.mmd`.

`./bin/qedesk blueprint` then runs Lean Blueprint and writes:

```text
blueprint/web/index.html
blueprint/web/dep_graph_document.html
```

The generated web pages use Lean Blueprint's original plasTeX dependency graph
renderer. QEDesk adds only a small bottom-right view switcher linking the
Blueprint page and the dependency graph page. For the upstream viewing flow,
run:

```bash
./bin/qedesk serve
```

Then open:

```text
http://localhost:8000/
http://localhost:8000/dep_graph_document.html
```

The current mapper is intentionally conservative: it trusts explicit QEDesk
markers for graph structure, handles checked Lean declarations and a small set
of statement renderings, then falls back to a code rendering for unfamiliar
statements.

QEDesk comment markers are safe LaTeX comments:

```tex
% QEDesk[node=mem_power_set][kind=lemma][title=Membership in the power set][lean=mem_power_set][status=checked]
% QEDesk[uses=def_power_set]
```

## Editor Setup

Start the container first:

```bash
./bin/qedesk start
```

Then point your editor's Lean executable or Lean server command to one of these
wrappers.

For WSL, Linux, or macOS:

```text
bin/lean
```

For a native Windows editor:

```text
bin\lean.bat
```

The wrapper forwards LSP traffic into the running container:

```bash
docker compose exec -T qedesk lake serve
```

## Distribution Notes

Commit source and configuration files, not generated artifacts. The repository
is set up to ignore local Docker/Lean/LaTeX outputs such as `.lake/`, `build/`,
temporary Lean Blueprint cache output such as `blueprint/web/`, and LaTeX
auxiliary files.

Commit `lake-manifest.json`. It locks the exact `mathlib4`, Aesop,
ProofWidgets, import-graph, LeanSearchClient, and related Lake dependency
revisions used by this project.

To remove the local container and image:

```bash
./bin/qedesk docker-clean
```

This also removes the QEDesk Docker volume that stores `.lake`.

QEDesk pins Lean through `lean-toolchain` so other users get the same Lean
version when they build the project.

For the best Windows performance, keep active QEDesk projects in the WSL Linux
filesystem rather than under `/mnt/c/...` when possible. The current layout
still works from `/mnt/c/...`, but large Lean builds and file watching are
usually faster inside the Linux filesystem.

## License

MIT. See `LICENSE`.
