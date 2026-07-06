# AI Agent Instructions

QEDesk is an undergraduate mathematics workstation that combines Lean 4,
LaTeX, Python, and MCP-based assistant tooling in one container.

Rules for AI agents:

1. Do not write complete proofs on behalf of the student.
2. Before suggesting edits around a `sorry`, use `lean-lsp-mcp` to inspect
   the current goal state. Provide repair hints, tactic suggestions, and
   explanations rather than a full finished proof.
3. When editing LaTeX notes, preserve existing mathematical formatting.
   Never damage or rewrite established environments such as `minted`,
   theorem/proof blocks, displayed equations, labels, or references unless
   the user explicitly asks for that change.
