define i32 @multi_hoist(i32 %n, i32 %a, i32 %b, i32 %c) {
entry:
  br label %loop

loop:
  %i = phi i32 [ 0, %entry ], [ %i.next, %loop ]
  %sum = phi i32 [ 0, %entry ], [ %new_sum, %loop ]
  
  ; Independent hoistable computations
  %calc1 = mul i32 %a, %b
  %calc2 = add i32 %c, 42
  %calc3 = sub i32 %calc1, %calc2
  %calc4 = shl i32 %calc3, 1
  
  ; Use with loop variable
  %result = add i32 %calc4, %i
  %new_sum = add i32 %sum, %result
  
  %i.next = add i32 %i, 1
  %cond = icmp slt i32 %i.next, %n
  br i1 %cond, label %loop, label %exit

exit:
  ret i32 %new_sum
}
