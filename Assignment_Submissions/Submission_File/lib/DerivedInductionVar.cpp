/* DerivedInductionVar.cpp 
 *
 * This pass detects derived induction variables using ScalarEvolution.
 *
 * Compatible with New Pass Manager
*/

#include "llvm/IR/PassManager.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Value.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Analysis/ScalarEvolutionExpressions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

using namespace llvm;

namespace {

class DerivedInductionVar
    : public PassInfoMixin<DerivedInductionVar> {
public:
  PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM) {
    auto &LI = AM.getResult<LoopAnalysis>(F);
    auto &SE = AM.getResult<ScalarEvolutionAnalysis>(F);

    // Helper lambda to recursively analyze and transform loops and subloops
    std::function<void(Loop*)> analyzeAndTransformLoop = [&](Loop *L) {
      errs() << "Analyzing loop in function " << F.getName() << ":\n";
      BasicBlock *Header = L->getHeader();
      if (!Header)
        return;

      // First, identify the primary induction variable (canonical IV)
      PHINode *PrimaryIV = nullptr;
      for (PHINode &PN : Header->phis()) {
        if (!PN.getType()->isIntegerTy())
          continue;
        const SCEV *S = SE.getSCEV(&PN);
        if (auto *AR = dyn_cast<SCEVAddRecExpr>(S)) {
          if (AR->isAffine() && AR->getLoop() == L) {
            // Check if this is a simple {start,+,1} pattern (primary IV)
            if (const SCEVConstant *StepSC = dyn_cast<SCEVConstant>(AR->getStepRecurrence(SE))) {
              if (StepSC->getAPInt() == 1) {
                PrimaryIV = &PN;
                errs() << "  Primary induction variable: " << PN.getName() 
                       << " = {" << *AR->getStart() << ",+,1}<" << L->getHeader()->getName() << ">\n";
                break;
              }
            }
          }
        }
      }

      // If we don't have a primary IV, try to find any IV to use as base
      if (!PrimaryIV) {
        for (PHINode &PN : Header->phis()) {
          if (!PN.getType()->isIntegerTy())
            continue;
          const SCEV *S = SE.getSCEV(&PN);
          if (auto *AR = dyn_cast<SCEVAddRecExpr>(S)) {
            if (AR->isAffine() && AR->getLoop() == L) {
              PrimaryIV = &PN;
              errs() << "  Using as base IV: " << PN.getName() << "\n";
              break;
            }
          }
        }
      }

      // Now eliminate derived induction variables
      SmallVector<PHINode*, 8> ToEliminate;
      for (PHINode &PN : Header->phis()) {
        if (!PN.getType()->isIntegerTy() || &PN == PrimaryIV)
          continue;
        const SCEV *S = SE.getSCEV(&PN);
        if (auto *AR = dyn_cast<SCEVAddRecExpr>(S)) {
          if (AR->isAffine() && AR->getLoop() == L) {
            ToEliminate.push_back(&PN);
          }
        }
      }

      // Eliminate derived IVs
      for (PHINode *DerivedIV : ToEliminate) {
        const SCEV *S = SE.getSCEV(DerivedIV);
        if (auto *AR = dyn_cast<SCEVAddRecExpr>(S)) {
          const SCEV *Start = AR->getStart();
          const SCEV *Step = AR->getStepRecurrence(SE);
          
          errs() << "  Eliminating derived induction variable: " << DerivedIV->getName()
                 << " = {" << *Start << ",+," << *Step << "}<" << L->getHeader()->getName() << ">\n";

          // Try to get constant values for start and step
          Value *StartVal = nullptr;
          Value *StepVal = nullptr;
          
          if (const SCEVConstant *SC = dyn_cast<SCEVConstant>(Start)) {
            StartVal = ConstantInt::get(DerivedIV->getType(), SC->getAPInt());
          }
          if (const SCEVConstant *SC = dyn_cast<SCEVConstant>(Step)) {
            StepVal = ConstantInt::get(DerivedIV->getType(), SC->getAPInt());
          }

          if (StartVal && StepVal && PrimaryIV) {
            // Replace all uses of the derived IV with start + step * primaryIV
            SmallVector<User*, 8> Users(DerivedIV->users());
            for (User *U : Users) {
              if (Instruction *UseInst = dyn_cast<Instruction>(U)) {
                if (L->contains(UseInst) && UseInst != DerivedIV) {
                  IRBuilder<> Builder(UseInst);
                  Value *Mul = Builder.CreateMul(StepVal, PrimaryIV, "eliminated.iv.mul");
                  Value *NewVal = Builder.CreateAdd(StartVal, Mul, "eliminated.iv");
                  UseInst->replaceUsesOfWith(DerivedIV, NewVal);
                  errs() << "    Replaced use in: " << *UseInst << "\n";
                }
              }
            }

            // Remove the derived IV if it has no more uses
            if (DerivedIV->use_empty()) {
              errs() << "    Removed derived IV: " << DerivedIV->getName() << "\n";
              DerivedIV->eraseFromParent();
            } else {
              errs() << "    Could not remove " << DerivedIV->getName() << " (still has uses)\n";
            }
          } else {
            errs() << "    Cannot eliminate " << DerivedIV->getName() << " (non-constant start/step)\n";
          }
        }
      }

      // Recursively analyze and transform subloops (requirement 2a: handle inner loops)
      for (Loop *SubL : L->getSubLoops()) {
        analyzeAndTransformLoop(SubL);
      }
    };

    // Process all loops, including nested loops
    for (Loop *L : LI) {
      analyzeAndTransformLoop(L);
    }
    return PreservedAnalyses::none();
  }
};

} // namespace

// Register the pass
llvm::PassPluginLibraryInfo getDerivedInductionVarPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION, "DerivedInductionVar", LLVM_VERSION_STRING,
          [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, FunctionPassManager &FPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                  if (Name == "derived-iv") {
                    FPM.addPass(DerivedInductionVar());
                    return true;
                  }
                  return false;
                });
          }};
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return getDerivedInductionVarPluginInfo();
}
