# QEDesk Codex Install Guide

This guide is for using QEDesk from a fresh Codex workspace. It is intentionally
source-first: clone the repository, read the agent rules, and only build the
Docker workstation if the task actually needs Lean, LaTeX, MCP, or OpenRouter
runtime checks.

## 1. Clone The Repository

Prefer a durable WSL/Linux path rather than a temporary Codex working folder:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/dev-heps/QEDesk.git
cd QEDesk
```

If Codex already opened the repository in a temporary workspace, make sure all
changes are pushed before deleting that workspace:

```bash
git status
git remote -v
git push origin main
```

## 2. Read The Control Files

Before making changes, inspect the files that define QEDesk's behavior:

```bash
sed -n '1,220p' AGENTS.md
sed -n '1,220p' docs/ARCHITECTURE.md
sed -n '1,220p' docs/DATA_CONTRACTS.md
sed -n '1,220p' docs/orchestration.md
```

The core rule is:

```text
AI audits and proposes. Lean verifies.
```

Do not treat model output as a proof until Lean accepts it.

## 3. Local Secrets

OpenRouter keys are local-only. Never commit `.env`.

```bash
cp .env.example .env
```

Then edit `.env` locally:

```text
OPENROUTER_API_KEY=...
```

Use dry runs before real model calls:

```bash
./bin/qedesk audit --dry-run --max-nodes 1 src/main.tex
```

## 4. Optional Runtime Build

Only run Docker when the task requires actual Lean, LaTeX, Blueprint, MCP, or
router execution:

```bash
./bin/qedesk start
./bin/qedesk prepare
./bin/qedesk lean
./bin/qedesk pdf
```

The first build can be large because it creates a Docker image and a Lean
Mathlib cache volume. Later Lean builds are much faster if the cache is kept.

## 5. Worksheet Workflow

For a new problem, create a worksheet instead of overwriting old examples:

```bash
./bin/qedesk new set-theory/power-set --title "Power Set"
./bin/qedesk lean worksheets/set-theory/power-set
./bin/qedesk pdf worksheets/set-theory/power-set
./bin/qedesk audit --dry-run worksheets/set-theory/power-set
```

Generated worksheet outputs are ignored by Git.

## 6. Cleanup

Remove local generated files:

```bash
./bin/qedesk clean
```

Inspect local and Docker storage:

```bash
./bin/qedesk storage
```

Remove the QEDesk Docker container, image, and Lean cache volume when the local
runtime is no longer needed:

```bash
./bin/qedesk docker-clean
docker builder prune -f
```

On Windows, WSL VHDX files may stay large after deletion. From PowerShell:

```powershell
wsl --shutdown
wsl --manage Ubuntu-22.04 --set-sparse true
wsl --manage docker-desktop --set-sparse true
```

## 7. What To Commit

Commit source, documentation, scripts, and configuration templates.

Do not commit:

```text
.env
build/
outputs/
.lake/
blueprint/web/
worksheets/**/build/
worksheets/**/blueprint/web/
```

Before pushing:

```bash
git status
git grep -n -E "OPENROUTER_API_KEY=[s]k-|[s]k-or-v1-" || true
git push origin main
```
