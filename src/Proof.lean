import Mathlib.Data.Set.Basic
import Mathlib.FieldTheory.Finite.Basic

universe u v

section ImagePreimage

variable {A : Type u} {B : Type v}

theorem mem_of_mem_image_preimage
    (f : A -> B) (B1 : Set B) {b : B}
    (hb : Set.image f (Set.preimage f B1) b) :
    B1 b := by
  cases hb with
  | intro a ha =>
      cases ha with
      | intro ha hfa =>
          cases hfa
          exact ha

theorem image_preimage_subset
    (f : A -> B) (B1 : Set B) :
    Set.image f (Set.preimage f B1) <= B1 := by
  intro b hb
  exact mem_of_mem_image_preimage f B1 hb

end ImagePreimage

section FermatLittle

theorem fermat_little_modEq
    {p a : Nat} (hp : p.Prime) (ha : a.Coprime p) :
    Nat.ModEq p (a ^ (p - 1)) 1 :=
  Nat.ModEq.pow_card_sub_one_eq_one hp ha

end FermatLittle
