# Contributing to QEDesk

Thanks for helping improve QEDesk.

## Local Setup

```bash
make start
make build-lean
./bin/qedesk audit --dry-run --max-nodes 1 src/main.tex
make pdf
```

Use `make shell` if you need to inspect the container directly.

## Project Style

- Keep the default workflow simple: Docker, Make, Lean, LaTeX, and Python.
- Prefer reproducible configuration over machine-specific setup.
- Keep generated files out of commits.
- Preserve LaTeX math environments and `minted` blocks unless a change
  explicitly requires editing them.
- For Lean examples, keep proofs small and educational.

## Pull Request Checklist

- `make build-lean` succeeds.
- `./bin/qedesk audit --dry-run --max-nodes 1 src/main.tex` succeeds.
- `make pdf` succeeds.
- New generated files are ignored or removed.
- README or comments are updated when commands or workflow change.
