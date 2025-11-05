; Test case for induction variable elimination
; This test has multiple derived induction variables that should be eliminated

define void @test_iv_elimination(i32 %n) {
entry:
  br label %loop

loop:                                             ; preds = %loop, %entry
  %i = phi i32 [ 0, %entry ], [ %i.next, %loop ]          ; Primary IV: {0,+,1}
  %derived1 = phi i32 [ 10, %entry ], [ %derived1.next, %loop ]  ; Derived IV: {10,+,2}
  %derived2 = phi i32 [ 5, %entry ], [ %derived2.next, %loop ]   ; Derived IV: {5,+,3}
  
  ; Use the derived induction variables
  %sum = add i32 %derived1, %derived2
  %result = mul i32 %sum, %i
  
  ; Update induction variables
  %i.next = add i32 %i, 1
  %derived1.next = add i32 %derived1, 2
  %derived2.next = add i32 %derived2, 3
  
  ; Loop condition
  %cond = icmp slt i32 %i.next, %n
  br i1 %cond, label %loop, label %exit

exit:                                             ; preds = %loop
  ret void
}

; Nested loop test case
define void @nested_iv_test(i32 %n, i32 %m) {
entry:
  br label %outer.loop

outer.loop:                                       ; preds = %outer.inc, %entry
  %outer.i = phi i32 [ 0, %entry ], [ %outer.i.next, %outer.inc ]        ; Primary outer IV
  %outer.derived = phi i32 [ 100, %entry ], [ %outer.derived.next, %outer.inc ] ; Derived outer IV: {100,+,5}
  br label %inner.loop

inner.loop:                                       ; preds = %inner.loop, %outer.loop
  %inner.j = phi i32 [ 0, %outer.loop ], [ %inner.j.next, %inner.loop ]  ; Primary inner IV
  %inner.derived1 = phi i32 [ 0, %outer.loop ], [ %inner.derived1.next, %inner.loop ] ; Derived inner IV: {0,+,2}
  %inner.derived2 = phi i32 [ 10, %outer.loop ], [ %inner.derived2.next, %inner.loop ] ; Derived inner IV: {10,+,4}
  
  ; Use derived IVs
  %inner.sum = add i32 %inner.derived1, %inner.derived2
  %combined = add i32 %inner.sum, %outer.derived
  
  ; Update inner IVs
  %inner.j.next = add i32 %inner.j, 1
  %inner.derived1.next = add i32 %inner.derived1, 2
  %inner.derived2.next = add i32 %inner.derived2, 4
  
  %inner.cond = icmp slt i32 %inner.j.next, %m
  br i1 %inner.cond, label %inner.loop, label %outer.inc

outer.inc:                                        ; preds = %inner.loop
  %outer.i.next = add i32 %outer.i, 1
  %outer.derived.next = add i32 %outer.derived, 5
  %outer.cond = icmp slt i32 %outer.i.next, %n
  br i1 %outer.cond, label %outer.loop, label %exit

exit:                                             ; preds = %outer.inc
  ret void
}