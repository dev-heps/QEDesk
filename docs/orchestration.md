# QEDesk Token-Efficient Orchestration

This note is the QEDesk v0.3 design target for budget-aware AI orchestration.
It turns the current research direction into an engineering policy for using
OpenRouter models while keeping Lean 4 as the final verifier.

The current repository already wires Lean, Lean Blueprint, `lean-lsp-mcp`,
OpenCode configuration, the QEDesk DAG sidecar, and a first OpenRouter router
prototype. The router is intentionally conservative: it creates compact local
prompts, selects a model tier, and records real call cost, but it does not
replace Lean verification or perform autonomous full-proof generation.

## Research Synthesis

| Reference | QEDesk-relevant takeaway |
| --- | --- |
| [Goedel-Architect](https://arxiv.org/abs/2606.06468) | Start with a graph-only blueprint, then refine failing leaves instead of re-emitting whole proofs. Treat the blueprint as a token-saving device. |
| [EconProver](https://arxiv.org/html/2509.12603v1) | Avoid unconditional multi-sample chain-of-thought. Switch longer reasoning on only when cheap-model uncertainty or repeated Lean failure justifies it. |
| [Evaluation of LLMs for Mathematical Formalization in Lean](https://arxiv.org/html/2606.05632v1) | Iterative refinement with Lean feedback is usually more useful than repeated independent proof attempts. |
| [FrugalGPT](https://arxiv.org/abs/2305.05176) | Use a cascade of cheaper and stronger models rather than a single expensive model for every step. |
| [Dynamic Model Routing and Cascading](https://arxiv.org/html/2603.04445v2) | Keep routing outside prompts. Make routing decisions from measurable signals such as length, dependency depth, failure count, uncertainty, and prior outcomes. |
| [UCCI](https://arxiv.org/abs/2605.18796) | Calibrate escalation thresholds from local workload outcomes instead of hard-coding confidence cutoffs forever. |
| [SelfBudgeter](https://arxiv.org/html/2505.11274v4) | Tell the model the remaining answer budget and constrain output length to prevent overthinking. |
| [Adaptive Test-Time Compute Allocation](https://arxiv.org/html/2604.14853v1) | Cap total worksheet cost and allocate compute dynamically across nodes under that global budget. |

## Core Policy

QEDesk should be a budgeted blueprint refinement engine.

It should not send the whole project, whole conversation, whole Mathlib context,
or whole LaTeX note to a large reasoning model on every iteration. It should
prefer:

1. local-node-plus-neighbor context;
2. cheap-first model cascades;
3. Lean-error-driven retries;
4. early stopping after Lean success;
5. explicit token and cost logging.

## Pipeline And Model Tiers

```text
student note
-> audit
-> blueprint
-> formalize
-> Lean check
-> repair
-> verify
```

| Stage | Primary model | Escalation model | Notes |
| --- | --- | --- | --- |
| Audit | DeepSeek V4 Flash | DeepSeek V4 Pro | Natural-language critique of the student draft. Use compact JSON and no long proof generation. |
| Blueprint | DeepSeek V4 Flash | DeepSeek V4 Pro | Emit definitions, lemmas, theorem nodes, and dependencies. Escalate only disconnected or contradictory subgraphs. |
| Formalize | DeepSeek V4 Flash | DeepSeek V4 Pro | Generate Lean statement skeletons, not complete proofs. Keep node context small. |
| Lean check | Lean 4 server | None | Lean is the authority. No model can mark a node checked. |
| Repair | DeepSeek V4 Flash | DeepSeek V4 Pro, then DeepSeek R1 | Include only the current goal, offending line, and short Lean error excerpt. |
| Verify | Lean 4 server | None | Final acceptance requires a successful Lean build or MCP check. |

The default cascade is:

```text
Flash -> Pro -> R1
```

R1-class reasoning should be reserved for hidden-premise checks,
counterexample search, quantifier drift, or repeated repair failures.

## Token Budget Policy

These are initial defaults for student homework use. They should live in a
configuration file rather than prompts.

| Limit | Default | Rationale |
| --- | ---: | --- |
| Worksheet total | 12,000 input+output tokens | Small enough for routine OpenRouter use; forces local context discipline. |
| Per blueprint node | 384 input + 256 output tokens | Enough for a statement, up to three parent lemmas, and a compact repair. |
| Flash retries per node | 2 | Cheap local refinement before escalation. |
| Pro retries per node | 1 | Stronger planner should not loop. |
| R1 retries per node | 0 | Use once as a critic, not as a search loop. |
| Parent context | At most 3 nodes | Avoid full-DAG prompt bloat. |
| Lean error excerpt | At most 80 lines, preferably less | Send the actionable error, not the whole trace. |

Early-stop rules:

1. If Lean accepts the node, stop immediately.
2. If remaining budget is below `unchecked_nodes * 800`, stop model calls and
   ask the student to choose a node.
3. If three successive nodes exceed their retry quota, ask for clarification
   or a narrower target.
4. If the model changes the theorem statement without explicit approval, reject
   the repair and log `statement_drift`.

## Model Prices

Do not hard-code model prices in prompts. Prices change across providers and
over time.

Store rates in a local config such as `qedesk-router.json`:

```json
{
  "models": {
    "cheap_worker": {
      "id": "deepseek/deepseek-v4-flash",
      "input_usd_per_mtok": 0.09,
      "output_usd_per_mtok": 0.18
    },
    "strong_planner": {
      "id": "deepseek/deepseek-v4-pro",
      "input_usd_per_mtok": 0.435,
      "output_usd_per_mtok": 0.87
    },
    "deep_critic": {
      "id": "deepseek/deepseek-r1",
      "input_usd_per_mtok": 0.70,
      "output_usd_per_mtok": 2.50
    }
  }
}
```

The values above are example OpenRouter-style rates and must be refreshed
before relying on a cost estimate.

## Cost Ledger

Every model call should append a row to a SQLite table or JSONL ledger.

| Column | Example |
| --- | --- |
| `worksheet_id` | `hw1-prob3` |
| `node_id` | `mem_of_mem_image_preimage` |
| `stage` | `repair` |
| `model_name` | `deepseek/deepseek-v4-flash` |
| `prompt_tokens` | `210` |
| `completion_tokens` | `87` |
| `estimated_cost_usd` | `0.000034` |
| `elapsed_ms` | `840` |
| `outcome` | `pass`, `fail`, `escalated`, `abandoned` |
| `lean_status` | `unchecked`, `ok`, `error` |
| `error_type` | `type_mismatch`, `unknown_identifier`, `statement_drift` |

Useful metrics:

```sql
SELECT
  SUM(estimated_cost_usd) / COUNT(DISTINCT node_id) AS cost_per_checked_node
FROM ledger
WHERE worksheet_id = ? AND lean_status IN ('ok', 'error');
```

```sql
SELECT
  SUM(estimated_cost_usd) AS cost_per_verified_problem
FROM ledger
WHERE worksheet_id = ?;
```

QEDesk should report both successful and failed spend. Failed retries are part
of the real cost of a workflow.

## Routing Algorithm

Initial heuristic:

```text
route(node_ctx):
  if worksheet_budget_spent >= hard_cap:
    return ask_student_or_stop

  if node_ctx.lean_status == "ok":
    return stop

  if node_ctx.failure_count == 0:
    return Flash

  if node_ctx.failure_count <= 2 and node_ctx.error_is_local:
    return Flash

  if node_ctx.statement_drift or node_ctx.dependency_cycle:
    return Pro

  if node_ctx.failure_count > 2 and node_ctx.error_is_conceptual:
    return Pro

  if node_ctx.hidden_premise or node_ctx.quantifier_drift:
    return R1

  return Flash
```

Later calibration target:

```text
cheap_model_margin -> estimated_error_probability
estimated_error_probability >= tau -> escalate
```

`tau` should be calibrated per course or assignment set using ledger outcomes.
Until calibration exists, use conservative heuristics:

1. escalate after repeated identical Lean errors;
2. escalate on statement drift;
3. escalate on dependency cycles;
4. do not escalate on syntax errors that can be locally repaired.

## Prompt Strategy

Send only:

1. current node statement;
2. node kind and status;
3. up to three parent lemmas or definitions;
4. student draft snippet, at most 80 tokens;
5. current Lean goal state or short error excerpt;
6. remaining worksheet and node budget;
7. required JSON schema.

Never send wholesale:

1. full `src/Proof.lean`;
2. full `src/main.tex`;
3. full Mathlib context;
4. prior hidden reasoning;
5. entire previous chat transcript;
6. long repeated Lean traces.

Require compact structured output:

```json
{
  "status": "repair_hint",
  "node_id": "...",
  "classification": "missing_justification",
  "minimal_hint": "...",
  "candidate_statement": "...",
  "needs_escalation": false,
  "confidence": 0.72
}
```

Prompt header:

```text
Short answers only.
Do not write a full proof.
Use at most {remaining_output_tokens} output tokens.
Return JSON only.
Lean is the authority; call unchecked work a candidate.
```

## Implementation Plan

Current QEDesk has `bin/qedesk`, `tools/qedesk_sync.py`,
`tools/qedesk_router.py`, `tools/qedesk_ledger.py`, `qedesk-router.json`,
`opencode.json`, and the generated DAG sidecar. The orchestration layer should
fit this layout first; a package can be introduced later if the scripts grow.

| File | Action |
| --- | --- |
| `qedesk-router.json` | Model IDs, rates, budgets, retry limits, escalation thresholds. |
| `tools/qedesk_router.py` | Implement routing decisions from node context and ledger history; call OpenRouter through the OpenAI-compatible API. |
| `tools/qedesk_ledger.py` | SQLite cost ledger helpers. |
| `schemas/qedesk-audit.schema.json` | Validate model audit output. |
| `schemas/qedesk-ledger.schema.json` | Validate JSONL ledger rows if SQLite is not used. |
| `bin/qedesk` and `bin/qedesk.bat` | Add `audit`, `formalize`, `repair`, `cost`, and `route` commands. |
| `opencode.json` | Add budget-aware agent prompts and route names. |
| `docs/INTEGRATIONS.md` | Mark each command as `wired` only after implementation exists. |

Proposed commands:

```bash
./bin/qedesk audit src/main.tex
./bin/qedesk audit --dry-run --max-nodes 1 src/main.tex
./bin/qedesk formalize src/main.tex --node mem_of_mem_image_preimage
./bin/qedesk repair src/main.tex --node mem_of_mem_image_preimage --lean-error "..."
./bin/qedesk route mem_of_mem_image_preimage
./bin/qedesk cost
```

Implemented now:

1. local-node prompt building from QEDesk markers in `src/main.tex`;
2. Flash -> Pro -> R1 tier selection from retry/error heuristics;
3. OpenRouter calls through the Python `openai` client;
4. dry-run mode that shows the exact prompt without spending tokens;
5. SQLite cost summaries through `./bin/qedesk cost`.

Still roadmap:

1. schema validation for every model response;
2. automatic conversion from audit JSON into new QEDesk nodes;
3. MCP goal-state capture directly from the current editor cursor;
4. learned uncertainty calibration from local worksheet outcomes.

## Risks And Guardrails

| Risk | Guardrail |
| --- | --- |
| Statement drift during repair | Re-run Lean after each patch; reject theorem changes unless explicitly approved. |
| Hidden premises accepted | Audit new assumptions and mark them as gap nodes before formalization. |
| Over-escalation | Calibrate `tau` from ledger outcomes; cap Pro and R1 calls. |
| Infinite retry loops | Enforce worksheet and per-node token caps. |
| Long-context waste | Send local-node-plus-neighbor context only. |
| False confidence from AI JSON | Treat JSON as a candidate; Lean or explicit human review decides status. |
| Price drift | Refresh model rate config and never bake costs into prompts. |

## Default Student Policy

```yaml
model_order:
  - deepseek/deepseek-v4-flash
  - deepseek/deepseek-v4-pro
  - deepseek/deepseek-r1
max_tokens_worksheet: 12000
max_input_tokens_per_node: 384
max_output_tokens_per_node: 256
flash_retries_per_node: 2
pro_retries_per_node: 1
r1_retries_per_node: 0
uncertainty_threshold: 0.15
context_scope: local-node-plus-three-parents
early_stop_on_lean_success: true
```

The target is not a fixed dollar claim. The target is a measurable workflow:

```text
minimize cost_per_verified_problem
subject to:
  Lean remains the final verifier
  no full-proof zero-shot generation
  student-facing hints remain local and educational
```
