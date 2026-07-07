# QEDesk Architecture

QEDesk is an undergraduate mathematics workstation for studying proof
quality. Its goal is not to find one perfect model that writes complete
proofs. Its goal is to make a verification workflow that keeps working when
models change.

## Core Principle

AI is an auditor and candidate generator. Lean 4 is the final judge.

No model output is treated as true until Lean checks it. If Lean rejects a
statement, tactic, or proof candidate, QEDesk treats the candidate as
unverified regardless of how convincing the explanation sounds.

## Component Boundaries

QEDesk separates knowledge retrieval, proof-state communication, verification,
and model reasoning.

| Component | Responsibility | Non-Responsibility |
| --- | --- | --- |
| RAG | Retrieve mathlib lemmas, textbook definitions, prior notes, and examples. | Decide whether a proof is correct. |
| MCP | Expose Lean goal states, diagnostics, errors, and tactic feedback. | Store broad mathematical knowledge. |
| Lean 4 | Verify formal statements and proof candidates. | Explain pedagogy or repair natural-language prose. |
| AI | Audit local reasoning, propose subgoals, suggest candidate tactics, and explain failures. | Assert correctness without Lean verification. |
| LaTeX | Preserve the student's human-readable proof notebook. | Serve as the source of formal truth. |

The project-level data contracts are defined in `docs/DATA_CONTRACTS.md`.
That document fixes the QEDesk-specific DAG sidecar schema that is not an
upstream Lean Blueprint standard.

## Proof Loop

The expected QEDesk v0.2 workflow is:

1. Write or paste a natural-language proof in `src/main.tex`.
2. Identify the assumptions, variables, quantifiers, and exact goal.
3. Split the proof into local inference steps.
4. Audit each step as verified, missing justification, false, or unclear.
5. Build a blueprint: definitions, lemmas, dependencies, and target theorem.
6. Translate one local target or lemma into Lean in `src/Proof.lean`.
7. Run Lean through `./bin/qedesk lean` or the `qedesk_lean` MCP server.
8. Use Lean errors and goal states as feedback.
9. Repair the blueprint or local proof step.
10. Update the LaTeX note with the lesson learned.

The loop is deliberately local. QEDesk should prefer verifying one inference
or lemma at a time over asking a model for a complete proof.

## Blueprint DAG

For nontrivial proofs, QEDesk should avoid direct zero-shot formalization.
Instead, it should first produce a small blueprint graph:

- nodes are definitions, facts, lemmas, or final goals;
- edges record dependency between nodes;
- each node has an informal statement and, when possible, a Lean target;
- failed Lean checks refine the relevant node, not the entire proof.

This mirrors modern proof-agent systems that separate high-level proof design
from local proof search.

QEDesk v0.2 keeps `src/main.tex` as the editable student note. Explicit
`% QEDesk[node=...]` and `% QEDesk[uses=...]` comments in that file are parsed
as the proof graph source. `qedesk sync` generates Lean Blueprint source at
`blueprint/src/content.tex`, a QEDesk JSON sidecar at `build/qedesk-dag.json`,
and a Mermaid sidecar at `build/qedesk-dag.mmd`. Lean Blueprint web output is
built under `blueprint/web/`. Automatic bidirectional sync is intentionally
unspecified until QEDesk has a real LaTeX parser.

For ongoing use, QEDesk supports independent worksheets under
`worksheets/<slug>/`. Each worksheet owns its own `main.tex`, `Proof.lean`,
`build/`, and `blueprint/` outputs. The root `src/` pair remains the default
starter workbook, while new exercises should usually be created with:

```bash
./bin/qedesk new number-theory/fermat-little
./bin/qedesk lean worksheets/number-theory/fermat-little
./bin/qedesk pdf worksheets/number-theory/fermat-little
./bin/qedesk audit --dry-run worksheets/number-theory/fermat-little
```

This keeps natural-language notes, Lean targets, generated graphs, and audit
history local to the problem being studied.

Generated outputs are disposable. `./bin/qedesk clean` removes local PDFs,
LaTeX logs, Blueprint HTML, and worksheet generated outputs while preserving
the OpenRouter cost ledger. Docker image and Lean cache storage are managed
separately; inspect them with `./bin/qedesk storage`.

## Local Verification

Natural-language proof auditing should use local typed justifications:

- What is the current state?
- What exact claim rewrites or extends that state?
- Which assumption, definition, theorem, or previous lemma justifies it?
- Does the quantifier direction match the intended use?
- Are all variables in scope?
- Is there a counterexample?

If a step cannot answer these questions, the agent must mark it as missing
justification or unclear instead of smoothing it into a finished proof.

Default gap labels are:

- `quantifier-jump`
- `missing-hypothesis`
- `missing-justification`
- `false-inference`
- `undefined-symbol`
- `ambiguous-expression`
- `set-membership-gap`
- `calculation-gap`
- `visual-dependence`
- `statement-drift`
- `unspecified`

Default hint levels are 0 through 4, where 0 only highlights the span and 4 is
a Lean candidate patch.

## Model Routing

Models are replaceable implementation details. The default routing is:

- DeepSeek V4 Pro: default proof-audit tutor and orchestrator.
- DeepSeek V4 Flash: low-cost helper for summaries, broad exploration, and
  repeated local checks.
- DeepSeek R1 family: deeper re-audit when a proof may hide a subtle logical
  gap.
- Prover-specific models: use only when available through OpenRouter or a
  stable local/custom endpoint, and always verify their candidates with Lean.

The practical metric is not benchmark score alone. QEDesk cares about cost per
successfully verified proof iteration.

The current router prototype is configured in `qedesk-router.json` and exposed
through:

```bash
./bin/qedesk audit --dry-run --max-nodes 1 src/main.tex
./bin/qedesk audit src/main.tex
./bin/qedesk formalize src/main.tex --node mem_of_mem_image_preimage
./bin/qedesk repair src/main.tex --node mem_of_mem_image_preimage --lean-error "..."
./bin/qedesk route mem_of_mem_image_preimage
./bin/qedesk cost
```

These commands produce audits, skeletons, repair hints, and cost summaries.
They do not turn AI output into a checked theorem; that still requires Lean.

## Deployment Questions

Before adding a new model or prover framework, answer:

1. Is it available through OpenRouter/OpenCode, or does it require self-hosting?
2. Can it call or cooperate with Lean through MCP?
3. Does it reduce cost per verified proof, not just cost per token?
4. Does it preserve local proof auditing instead of jumping to complete proofs?
5. Can it explain failure states in a way useful to a student?

## Integration Roadmap

QEDesk should integrate extra tools only when they improve the verification
loop without turning the workstation into an automatic proof writer.

Current implementation status is tracked in `docs/INTEGRATIONS.md`. The table
below is a roadmap, not a claim that these tools are already installed or
called by QEDesk.

| Tool | Role | QEDesk Use |
| --- | --- | --- |
| `mathlib4` | Lean mathematics library | Theorem grounding, examples, and real undergraduate formalization. Currently wired through `lakefile.lean`. |
| `Aesop` | White-box proof search tactic | Bounded tactic-family candidate generation in `qedesk-fast`. Currently available through mathlib. |
| `ProofWidgets4` | Goal and proof-state UI widgets | Future subgoal cards and proof-state visualization. Currently available through mathlib. |
| `Loogle` / `LeanSearchClient` | Theorem and definition search | Reduce hallucinated theorem links and support RAG. LeanSearchClient is available through mathlib; Loogle is not locally configured yet. |
| `doc-gen4` / `docgen-action` | Documentation generation | Publish course packs and proof-desk docs. |
| `import-graph` | Import dependency analysis | Keep course modules small and explain dependencies. |
| `verbose-lean4` | Controlled natural language bridge | Optional beginner mode for natural-language-to-Lean transition. |
| `Waterproof Editor` | Education-oriented proof UI | Future browser-style learning mode. |
| `LeanCopilot` / `Duper` | Automated premise or proof search | Research-only or high hint-level candidate generation. |

The first production-grade additions should be search and visualization
support, not unrestricted automatic proof generation.

## Current Interface

Use these commands from the project root in WSL:

```bash
./bin/qedesk start
./bin/qedesk prepare
./bin/qedesk lean
./bin/qedesk pdf
opencode
```

OpenCode should use `opencode.json`, which registers `qedesk_lean` as the
local MCP server:

```text
OpenCode -> ./bin/qedesk agent -> lean-lsp-mcp -> Lean/Lake
```

Humans should not run `./bin/qedesk agent` interactively. It is a stdio server
for MCP clients.

## Runtime Notes

For Windows users, the most responsive setup is usually:

```text
Windows + WSL2 + Linux filesystem + Docker Desktop WSL integration
```

Working directly under `/mnt/c/...` is convenient, but large Lean builds and
file watching are usually faster from the WSL Linux filesystem.

QEDesk mounts the project source into `/workspace` and stores `.lake` in a
Docker named volume. This keeps Mathlib dependency checkouts and build products
off the host bind mount, which is especially important on Windows.

Run `./bin/qedesk prepare` before launching OpenCode when possible. It performs
the Lean build that reduces first MCP timeout surprises.
