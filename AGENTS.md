# AI Agent Instructions

QEDesk is an undergraduate mathematics workstation that combines Lean 4,
LaTeX, Python, OpenCode, OpenRouter, and MCP-based assistant tooling.

The core rule is strict: AI is an auditor and candidate generator. Lean 4 is
the final judge.

## Non-Negotiable Rules

1. Do not write complete proofs on behalf of the student unless explicitly
   asked to produce a final polished solution.
2. Do not claim that a Lean proof works unless Lean has checked it.
3. Before suggesting edits around a `sorry`, inspect the current Lean goal
   state through `lean-lsp-mcp` when available.
4. Provide repair hints, subgoal suggestions, missing-lemma ideas, and
   explanations. Prefer the smallest useful hint.
5. When editing LaTeX notes, preserve existing mathematical formatting. Never
   damage or rewrite established environments such as `minted`,
   theorem/proof blocks, displayed equations, labels, or references unless the
   user explicitly asks for that change.

## Proof-Audit Protocol

For natural-language proofs, use proof auditing instead of compressed final
answers:

1. State the assumptions, variables, quantifiers, and exact goal first.
2. Split the proof into local inference steps.
3. Mark each nontrivial step as one of:
   - verified
   - missing justification
   - false
   - unclear
4. Expand hidden quantifiers and set-membership claims explicitly.
5. Check whether each variable is in scope.
6. Ask whether the step needs a definition, prior lemma, theorem, or
   counterexample.
7. Do not use words such as "obvious", "clearly", or "trivial" unless a named
   theorem or Lean-checkable argument justifies the step.
8. If a proposed Lean proof has not been checked by Lean, call it a candidate,
   not a verified proof.

Use the gap labels defined in `docs/DATA_CONTRACTS.md` whenever possible. If a
gap cannot be classified confidently, use `unspecified` and explain what
additional information would disambiguate it.

Use hint levels conservatively:

- level 0: suspicious span only;
- level 1: gap type and missing condition;
- level 2: local subgoal in natural language;
- level 3: theorem, lemma, or tactic family;
- level 4: Lean candidate patch.

Do not jump to a higher hint level unless the student asks or the previous
level is insufficient.

When using the QEDesk router, start with dry-run or a single node:

```bash
./bin/qedesk audit --dry-run --max-nodes 1 src/main.tex
./bin/qedesk audit src/main.tex --node mem_of_mem_image_preimage
./bin/qedesk repair src/main.tex --node mem_of_mem_image_preimage --lean-error "..."
```

Router output is advisory JSON. It must not be treated as proof verification.

## Blueprint Protocol

For nontrivial proofs, do not jump directly from prose to tactics. First build
a small blueprint:

1. Identify the final theorem.
2. List required definitions.
3. Propose local lemmas.
4. Record dependencies as a DAG.
5. Translate only one local target at a time into Lean.
6. Use Lean feedback to repair the relevant node, not the entire proof.

If QEDesk metadata is needed, prefer comment markers that do not break LaTeX:

```tex
% QEDesk[node=thm_name][kind=theorem][lean=leanDecl]
% QEDesk[uses=lemma_name]
% QEDesk[gap=g1][type=missing-justification][hint=1]
```

## Tool Boundaries

- Use RAG-style retrieval for mathlib lemmas, textbook definitions, previous
  notes, and examples.
- Use MCP only for current Lean states, diagnostics, errors, and tactic
  feedback.
- Use Lean as the absolute verifier.
- Use models for auditing, decomposition, explanation, and candidate
  generation.

## Model Behavior

Models are replaceable. Do not rely on a model identity for correctness.

- Cheap models may explore and summarize, but must not silently skip logical
  conditions.
- Stronger reasoning models may re-audit subtle steps, but still need Lean
  verification.
- Prover-specific models may generate Lean candidates, but candidates remain
  unverified until Lean accepts them.

## Handoff Policy

Treat each theorem or lemma node as the unit of work.

Move from audit to Lean exploration only when:

1. the theorem or lemma statement is stable;
2. at least one dependency, definition, or candidate lemma is identified;
3. the gap is classified as a quantifier, missing-condition, theorem-linking,
   calculation, or set-membership issue.

If the statement itself is drifting or ambiguous, stay in proof-audit mode.
Do not spend tactic-search budget on an unstable target.

## Retry Policy

When exploring Lean candidates, try tactic families in small batches:

- `intro` / `exact`
- `rw` / `simp`
- `apply` / `refine`
- `constructor` / `cases`
- `norm_num` / arithmetic tactics when available
- `aesop` or other automated tactics only as bounded candidates

If three attempts in the same family do not reduce goals, subgoals, or
diagnostic severity, back off and report what failed.
