* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

$onVerbatim

$ifi not "%gams.optdir%"=="" $if not dexist "%gams.optdir%" put_utility 'exec' / 'mkdir -p %gams.optdir%'

* ==== GAMS solver options ====
$if not set solver            $setglobal solver           "cplex"
$if not set solvelink         $setglobal solvelink        0
$if not set optfile           $setglobal optfile          1
$if not set holdfixed         $setglobal holdfixed        1
$if not set equlist           $setglobal equlist          0

* ==== REMix debug options ====
$ife %debug%<>0               $setglobal solvermethodi    "simplex"
$ife %debug%<>0               $setglobal names            1
$ife %debug%<>0               $setglobal iis              1

* ==== REMix solver defaults ====
$if not set solvermethod      $setglobal solvermethod     1
$if %solvermethod%=="0"       $setglobal solvermethodi    "auto"
$if %solvermethod%=="1"       $setglobal solvermethodi    "barrier"
$if %solvermethod%=="2"       $setglobal solvermethodi    "simplex"
$if %solvermethod%=="auto"    $setglobal solvermethodi    "auto"
$if %solvermethod%=="barrier" $setglobal solvermethodi    "barrier"
$if %solvermethod%=="simplex" $setglobal solvermethodi    "simplex"

$if not set passproblem       $setglobal passproblem      1
$if %passproblem%=="0"        $setglobal passproblemi     "auto"
$if %passproblem%=="1"        $setglobal passproblemi     "primal"
$if %passproblem%=="2"        $setglobal passproblemi     "dual"
$if %passproblem%=="auto"     $setglobal passproblemi     "auto"
$if %passproblem%=="primal"   $setglobal passproblemi     "primal"
$if %passproblem%=="dual"     $setglobal passproblemi     "dual"

$if not set ordering          $setglobal ordering         1
$if %ordering%=="0"           $setglobal orderingi        "auto"
$if %ordering%=="1"           $setglobal orderingi        "nd"
$if %ordering%=="2"           $setglobal orderingi        "amd"
$if %ordering%=="3"           $setglobal orderingi        "amf"
$if %ordering%=="auto"        $setglobal orderingi        "auto"
$if %ordering%=="nd"          $setglobal orderingi        "nd"
$if %ordering%=="amd"         $setglobal orderingi        "amd"
$if %ordering%=="amf"         $setglobal orderingi        "amf"

$if not set scaling           $setglobal scaling          1
$if %scaling%=="0"            $setglobal scalingi         "none"
$if %scaling%=="1"            $setglobal scalingi         "standard"
$if %scaling%=="2"            $setglobal scalingi         "aggressive"
$if %scaling%=="none"         $setglobal scalingi         "none"
$if %scaling%=="standard"     $setglobal scalingi         "standard"
$if %scaling%=="aggressive"   $setglobal scalingi         "aggressive"

$if not set densecol          $setglobal densecol         0
$if not set crossover         $setglobal crossover        0
$if not set threads           $setglobal threads          8
$if not set accuracy          $setglobal accuracy         1e-6
$if not set mipaccuracy       $setglobal mipaccuracy      1e-3
$if not set names             $setglobal names            0
$if not set iis               $setglobal iis              0
$if not set rerun             $setglobal rerun            0


* ==== setup optimization ====
if ((sum(nodesModelToCalc, 1)>40 or sum(timeModelToCalc, 1)>50) and not %equlist%,
   option limRow=0, limCol=0, solPrint=off;
else
   option limRow=100000, limCol=100000, solPrint=on;
);


* ==== Solver specific default values ====

$iftheni.solver %solver%=="cplex"
$ifi %solvermethodi%=="auto"      $setglobal lpmethod 0
$ifi %solvermethodi%=="simplex"   $setglobal lpmethod 2
$ifi %solvermethodi%=="barrier"   $setglobal lpmethod 4
$ifi %passproblemi%=="auto"       $setglobal predual 0
$ifi %passproblemi%=="primal"     $setglobal predual -1
$ifi %passproblemi%=="dual"       $setglobal predual 1
$ifi %orderingi%=="auto"          $setglobal barorder 0
$ifi %orderingi%=="nd"            $setglobal barorder 3
$ifi %orderingi%=="amd"           $setglobal barorder 1
$ifi %orderingi%=="amf"           $setglobal barorder 2
$ifi %scalingi%=="standard"       $setglobal scaind 0
$ifi %scalingi%=="none"           $setglobal scaind -1
$ifi %scalingi%=="aggressive"     $setglobal scaind 1
$if set accuracy                  $setglobal barepcomp %accuracy%
$if set mipaccuracy               $setglobal epgap %mipaccuracy%
$ife %crossover%=0                $setglobal solutiontype 2
$ife %densecol%>0                 $setglobal barcolnz %densecol%
$if not set quality               $setglobal quality 1
$if not set advind                $setglobal advind 0


$elseifi.solver %solver%=="gurobi"
* Gurobi "method" collides with REMix "method"
$ifi %solvermethodi%=="auto"      $setglobal gurobimethod -1
$ifi %solvermethodi%=="barrier"   $setglobal gurobimethod 2
$ifi %solvermethodi%=="simplex"   $setglobal gurobimethod 5
$ifi %passproblemi%=="auto"       $setglobal predual -1
$ifi %passproblemi%=="primal"     $setglobal predual 0
$ifi %passproblemi%=="dual"       $setglobal predual 1
$ifi %orderingi%=="nd"            $setglobal barorder 1
$ifi %orderingi%=="auto"          $setglobal barorder -1
$ifi %orderingi%=="amd"           $setglobal barorder 0
$ifi %scalingi%=="standard"       $setglobal scaleflag -1
$ifi %scalingi%=="none"           $setglobal scaleflag 0
$ifi %scalingi%=="aggressive"     $setglobal scaleflag 2
$if set accuracy                  $setglobal barconvtol %accuracy%
$if set mipaccuracy               $setglobal mipgap %mipaccuracy%
$ife %densecol%>0                 $setglobal GURO_PAR_BARDENSETHRESH %densecol%


$elseifi.solver %solver%=="copt"
$ifi %solvermethodi%=="auto"      $setglobal lpmethod 5
$ifi %solvermethodi%=="barrier"   $setglobal lpmethod 2
$ifi %solvermethodi%=="simplex"   $setglobal lpmethod 1
$ifi %passproblemi%=="auto"       $setglobal dualize -1
$ifi %passproblemi%=="primal"     $setglobal dualize 0
$ifi %passproblemi%=="dual"       $setglobal dualize 1
$ifi %orderingi%=="auto"          $setglobal barorder -1
$ifi %orderingi%=="amd"           $setglobal barorder 0
$ifi %orderingi%=="nd"            $setglobal barorder 1
$ifi %scalingi%=="standard"       $setglobal scaling 1
$ifi %scalingi%=="none"           $setglobal scaling 0
$if set accuracy                  $setglobal relgap %accuracy%


$elseifi.solver %solver%=="xpress"
$ifi %solvermethodi%=="barrier"   $setglobal algorithm "barrier"
$ifi %solvermethodi%=="simplex"   $setglobal algorithm "simplex"
$ifi %passproblemi%=="auto"       $setglobal dualize -1
$ifi %passproblemi%=="primal"     $setglobal dualize 0
$ifi %passproblemi%=="dual"       $setglobal dualize 1
$ifi %orderingi%=="auto"          $setglobal barOrder 0
$ifi %orderingi%=="amd"           $setglobal barOrder 1
$ifi %orderingi%=="amf"           $setglobal barOrder 2
$ifi %orderingi%=="nd"            $setglobal barOrder 3
$ifi %scalingi%=="standard"       $setglobal autoScaling -1
$ifi %scalingi%=="none"           $setglobal autoScaling 0
$ifi %scalingi%=="aggressive"     $setglobal autoScaling 3
$if set accuracy                  $setglobal barGapStop %accuracy%
$if set mipaccuracy               $setglobal mipRelStop %mipaccuracy%


$elseifi.solver %solver%=="highs"
$ifi %solvermethodi%=="auto"      $setglobal highssolver "choose"
$ifi %solvermethodi%=="barrier"   $setglobal highssolver "ipm"
$ifi %solvermethodi%=="simplex"   $setglobal highssolver "simplex"
$ifi %solvermethodi%=="pdlp"      $setglobal highssolver "pdlp"
$ifi %solvermethodi%=="choose"    $setglobal highssolver "choose"
$ifi %solvermethodi%=="ipm"       $setglobal highssolver "ipm"
$ifi %scalingi%=="standard"       $setglobal pdlp_scaling 1
$ifi %scalingi%=="none"           $setglobal pdlp_scaling 0
$ifi %scalingi%=="aggressive"     $setglobal pdlp_scaling 1


$elseifi.solver %solver%=="mosek"
$ifi %solvermethodi%=="auto"      $setglobal MSK_IPAR_OPTIMIZER "MSK_OPTIMIZER_FREE"
$ifi %solvermethodi%=="barrier"   $setglobal MSK_IPAR_OPTIMIZER "MSK_OPTIMIZER_INTPNT"
$ifi %solvermethodi%=="barrier"   $setglobal MSK_IPAR_MIO_ROOT_OPTIMIZER "MSK_OPTIMIZER_INTPNT"
$ifi %solvermethodi%=="simplex"   $setglobal MSK_IPAR_OPTIMIZER "MSK_OPTIMIZER_FREE_SIMPLEX"
$ifi %passproblemi%=="auto"       $setglobal MSK_IPAR_INTPNT_SOLVE_FORM "MSK_SOLVE_FREE"
$ifi %passproblemi%=="primal"     $setglobal MSK_IPAR_INTPNT_SOLVE_FORM "MSK_SOLVE_PRIMAL"
$ifi %passproblemi%=="dual"       $setglobal MSK_IPAR_INTPNT_SOLVE_FORM "MSK_SOLVE_DUAL"
$if not set presolve              $setglobal presolve -1
$ife %presolve%<>0                $setglobal MSK_IPAR_PRESOLVE_USE "MSK_PRESOLVE_MODE_FREE"
$ife %presolve%=0                 $setglobal MSK_IPAR_PRESOLVE_USE "MSK_PRESOLVE_MODE_OFF"
$ifi %orderingi%=="auto"          $setglobal MSK_IPAR_INTPNT_ORDER_METHOD "MSK_ORDER_METHOD_FREE"
$ifi %orderingi%=="amf"           $setglobal MSK_IPAR_INTPNT_ORDER_METHOD "MSK_ORDER_METHOD_APPMINLOC"
$ifi %scalingi%=="standard"       $setglobal MSK_IPAR_INTPNT_SCALING "MSK_SCALING_FREE"
$ifi %scalingi%=="none"           $setglobal MSK_IPAR_INTPNT_SCALING "MSK_SCALING_NONE"
$ife %densecol%>0                 $setglobal MSK_IPAR_INTPNT_OFF_COL_TRH %densecol%
$if set threads                   $setglobal MSK_IPAR_NUM_THREADS %threads%
$if set accuracy                  $setglobal MSK_DPAR_INTPNT_TOL_REL_GAP %accuracy%
$if set accuracy                  $setglobal MSK_DPAR_MIO_REL_GAP_CONST %accuracy%
$if set mipaccuracy               $setglobal MSK_DPAR_MIO_TOL_REL_GAP %mipaccuracy%


$elseifi.solver %solver%=="convert"


$elseifi.solver %solver%=="scip"


$else.solver
$abort "No valid solver specified. Available solvers are CPLEX, Gurobi, COPT, XPRESS, HiGHS, MOSEK, Convert, or SCIP."
$endif.solver


$setenv GDXCOMPRESS 1

option mip = %solver%;
option reslim = 1209600;
option optcr = %mipaccuracy%;
remix.threads = %threads%;
remix.optFile = %optfile%;
remix.solveLink = %solvelink%;
remix.holdFixed = %holdfixed%;

$offVerbatim