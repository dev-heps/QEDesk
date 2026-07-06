def S : List Nat :=
  [1, 2, 3]

def powerSetS : List (List Nat) :=
  [
    [],
    [1],
    [2],
    [3],
    [1, 2],
    [1, 3],
    [2, 3],
    [1, 2, 3]
  ]

def usesOnlyElementsOfS (xs : List Nat) : Bool :=
  xs.all (fun n => (n == 1) || (n == 2) || (n == 3))

example : powerSetS.length = 8 := by
  native_decide

example : powerSetS.Nodup := by
  native_decide

example : powerSetS.all usesOnlyElementsOfS = true := by
  native_decide

example : powerSetS.contains ([] : List Nat) = true := by
  native_decide

example : powerSetS.contains [1, 2, 3] = true := by
  native_decide
