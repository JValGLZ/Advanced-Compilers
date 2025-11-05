define void @nested_loops(i32 %n, i32 %m) {
entry:
  br label %outer.loop

outer.loop:                                       ; preds = %outer.inc, %entry
  %i = phi i32 [ 0, %entry ], [ %i.next, %outer.inc ]
  br label %inner.loop

inner.loop:                                       ; preds = %inner.loop, %outer.loop
  %j = phi i32 [ 0, %outer.loop ], [ %j.next, %inner.loop ]
  %derived_j = mul i32 %j, 2                     ; derived IV: 2*j
  %derived_i = add i32 %i, 5                     ; derived IV: i+5
  
  ; Some computation using derived IVs
  %sum = add i32 %derived_i, %derived_j
  
  %j.next = add i32 %j, 1
  %inner.cond = icmp slt i32 %j.next, %m
  br i1 %inner.cond, label %inner.loop, label %outer.inc

outer.inc:                                        ; preds = %inner.loop
  %i.next = add i32 %i, 1
  %outer.cond = icmp slt i32 %i.next, %n
  br i1 %outer.cond, label %outer.loop, label %exit

exit:                                             ; preds = %outer.inc
  ret void
}
