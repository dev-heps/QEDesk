import Mathlib.Data.Set.Basic

/-!
QEDesk default workspace.

Use this root workspace as a small scratchpad, or create problem-specific
worksheets with:

  ./bin/qedesk new <slug>
-/

section DefaultWorkspace

theorem starter_example (P : Prop) (h : P) : P := by
  exact h

end DefaultWorkspace
