Part 1: Simple LICM

I have made a LICM pass that finds and hoists loop-invariant instructions out of loops. The algorithm adds all non-phi instructions in loop blocks to a worklist, iteratively identifies instructions whose operands are defined outside the loop or already marked as invariant, and continues until no new invariants are found. It also filters out instructions as given. Below the entire readme will be how to run it.

Tests
For testing I used the following files: 
    perfect_hoist_test.ll
    test2.ll
    test3.ll


To Run test: 
    # Test 1
    opt-21 -load-pass-plugin ./build/lib/libSimpleLICM.so -passes=simple-licm -S build/perfect_hoist_test.ll 2>&1 | grep "Hoisting:"

    # Test 2  
    opt-21 -load-pass-plugin ./build/lib/libSimpleLICM.so -passes=simple-licm -S build/test2.ll 2>&1 | grep "Hoisting:"

    # Test 3
    opt-21 -load-pass-plugin ./build/lib/libSimpleLICM.so -passes=simple-licm -S build/test3.ll 2>&1 | grep "Hoisting:"

My output: 

perfect_hoist_test.ll
Hoisting:   %x = add i32 %a, %b
Hoisting:   %y = mul i32 %x, 2
Hoisting:   %z = add i32 %y, %a

test2.ll
Hoisting:   %idx1 = add i32 %base, %offset
Hoisting:   %idx2 = sext i32 %idx1 to i64
Hoisting:   %ptr1 = getelementptr i32, ptr %arr, i64 %idx2

test3.ll
Hoisting:   %calc1 = mul i32 %a, %b
Hoisting:   %calc2 = add i32 %c, 42
Hoisting:   %calc3 = sub i32 %calc1, %calc2
Hoisting:   %calc4 = shl i32 %calc3, 1

Part 2
For part 2 I took the files two files and modified them after looking at the code to understand them. I extended the DerivedInductionVar.cpp so that it can identify IVs in the inner loops of loop nest and also extended the pass into a transformation pass that eliminates induction variables as mentioned. 

Tests: 
iv_elimination_test.ll
nested_loop_test.ll

To use AffineRecurrence:
opt-21 -load-pass-plugin ./build/lib/libAffineRecurrence.so -passes=affine-recurrence -S build/nested_loop_test.ll
opt-21 -load-pass-plugin ./build/lib/libAffineRecurrence.so -passes=affine-recurrence -S build/iv_elimination_test.ll

To use DerivedInductionVar
opt-21 -load-pass-plugin ./build/lib/libDerivedInductionVar.so -passes=derived-iv -S build/nested_loop_test.ll
opt-21 -load-pass-plugin ./build/lib/libDerivedInductionVar.so -passes=derived-iv -S build/iv_elimination_test.ll

An example of change should as below: 
BEFORE (Original test case):
%derived1 = phi i32 [ 10, %entry ], [ %derived1.next, %loop ]  ; Derived IV: {10,+,2}
%derived2 = phi i32 [ 5, %entry ], [ %derived2.next, %loop ]   ; Derived IV: {5,+,3}
%sum = add i32 %derived1, %derived2

AFTER (Eliminated derived IVs):
%eliminated.iv2 = add i32 10, %eliminated.iv.mul1  ; derived1 = 10 + 2*i
%eliminated.iv6 = add i32 5, %eliminated.iv.mul5   ; derived2 = 5 + 3*i
%sum = add i32 %eliminated.iv2, %eliminated.iv6


How to setup: 

The way I have organized this submission is that I have named the folders according to where I placed them in my LLVM-TUTOR folder. This is so that when it is tested, all that needs to be done is to drag and drop them into the folder. I have build and lib which are the only folders in LLVM-TUTOR that I added the files to. For example, the SimpleLICM.cpp file is under lib because I had it under lib in LLVM-TUTOR. Same with all files found under build. Doing this should let the pass test command lines work fine. If there is any issue, please let me know and I will immediately provide the entirety of my LLVM-TUTOR folder with all files included. I will likely attach the entire thing zipped either way to the submission folder or place it in github. 

Note: I was having issues with test cases so I used AI to generate the .ll files. That is the reason I have test case files with .ll instead of a compilation step. 