# QEDesk Blueprint Workspace

This directory is reserved for Lean Blueprint-compatible proof planning and
QEDesk sidecar artifacts.

QEDesk keeps `src/main.tex` as the student-facing note. Treat
`blueprint/src/content.tex` as generated output from `./bin/qedesk sync`.
The web visualization is generated under `blueprint/web/`, matching the
standard Lean Blueprint layout.

Recommended workflow:

1. Write the natural-language proof in `src/main.tex`.
2. Formalize one local claim in `src/Proof.lean`.
3. Run `./bin/qedesk sync` to regenerate `blueprint/src/content.tex`,
   `build/qedesk-dag.json`, and `build/qedesk-dag.mmd`.
4. Run `./bin/qedesk blueprint` to build the HTML dependency graph.

The current generator is intentionally conservative. It maps Lean declarations
and a small set of statement patterns; unfamiliar statements fall back to a
code rendering instead of pretending to understand them.
