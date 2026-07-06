# QEDesk

QEDesk is a containerized proof desk for undergraduate mathematics: Lean 4 for
formalization, LaTeX for notes, and Python for AI-assisted proof tooling.

Everything runs inside one Ubuntu-based Docker container. Your editor stays on
the host machine, while Lean, Lake, LaTeX, Python packages, and MCP tools share
the same container environment.

## Features

- Lean 4 and Lake pinned through `lean-toolchain`
- LaTeX with `latexmk`, `minted`, and science/math packages
- Python virtual environment with `openai`, `leanclient`, `lean-lsp-mcp`,
  `leanblueprint`, and `sympy`
- Host editor wrappers for Linux/WSL/macOS and native Windows
- A small `qedesk` command for the common workstation workflow

## Requirements

- Docker Desktop or Docker Engine with Docker Compose
- WSL, Linux, or macOS for the shell commands below

On Windows, use `bin\qedesk.bat` from PowerShell or run `./bin/qedesk` from WSL.

## Quick Start

```bash
./bin/qedesk start
./bin/qedesk lean
./bin/qedesk pdf
```

The first `qedesk start` builds the Docker image, so it can take several
minutes. Later starts should be much faster.

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
./bin/qedesk lean          # Build the Lean library
./bin/qedesk pdf           # Build build/main.pdf from src/main.tex
./bin/qedesk agent         # Run lean-lsp-mcp inside the container
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
./bin/qedesk lean
./bin/qedesk pdf
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
make build-lean
make pdf
```

## Project Layout

```text
.
|-- Dockerfile
|-- docker-compose.yml
|-- Makefile
|-- README.md
|-- AGENTS.md
|-- .env.example
|-- .dockerignore
|-- .gitignore
|-- lean-toolchain
|-- lakefile.lean
|-- bin/
|   |-- qedesk
|   |-- qedesk.bat
|   |-- lean
|   `-- lean.bat
`-- src/
    |-- Proof.lean
    `-- main.tex
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
`lake-manifest.json`, and LaTeX auxiliary files.

To remove the local container and image:

```bash
./bin/qedesk docker-clean
```

QEDesk pins Lean through `lean-toolchain` so other users get the same Lean
version when they build the project.

## License

MIT. See `LICENSE`.
