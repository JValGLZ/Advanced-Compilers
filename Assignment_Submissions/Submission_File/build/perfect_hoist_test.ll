define i32 @test_hoist(i32 %n, i32 %a, i32 %b) {
entry:
  br label %loop

loop:                                             ; preds = %loop, %entry
  %i = phi i32 [ 0, %entry ], [ %i.next, %loop ]
  %sum = phi i32 [ 0, %entry ], [ %new_sum, %loop ]
  
  ; These should be hoisted - they don't depend on loop variables
  %x = add i32 %a, %b
  %y = mul i32 %x, 2
  %z = add i32 %y, %a
  
  ; This uses the hoistable values plus loop variable
  %temp = add i32 %z, %i
  %new_sum = add i32 %sum, %temp
  
  %i.next = add i32 %i, 1
  %cond = icmp slt i32 %i.next, %n
  br i1 %cond, label %loop, label %exit

exit:                                             ; preds = %loop
  ret i32 %new_sum
}
