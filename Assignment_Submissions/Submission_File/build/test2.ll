define void @gep_hoist(ptr %arr, i32 %n, i32 %base, i32 %offset) {
entry:
  br label %loop

loop:
  %i = phi i32 [ 0, %entry ], [ %i.next, %loop ]
  
  ; These getelementptr should be hoisted
  %idx1 = add i32 %base, %offset
  %idx2 = sext i32 %idx1 to i64
  %ptr1 = getelementptr i32, ptr %arr, i64 %idx2
  
  ; Use with loop variable
  %val = load i32, ptr %ptr1
  %new_val = add i32 %val, %i
  store i32 %new_val, ptr %ptr1
  
  %i.next = add i32 %i, 1
  %cond = icmp slt i32 %i.next, %n
  br i1 %cond, label %loop, label %exit

exit:
  ret void
}
