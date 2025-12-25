* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

$onVerbatim

$iftheni.solver %solver%==cplex
file opt / "%gams.optdir%cplex.opt" /;
put opt;
$ife %names%=0         put "names no" /;
$ife %rerun%=0         put "rerun no" /;

$if set lpmethod       put "lpmethod %lpmethod%" /;
$if set threads        put "threads %threads%" /;
$if set barorder       put "barorder %barorder%" /;

$if set advind         put "advind %advind%" /;
$if set preind         put "preind %preind%" /;
$if set scaind         put "scaind %scaind%" /;
$if set predual        put "predual %predual%" /;

$if set baralg         put "baralg %baralg%" /;
$if set barstartalg    put "barstartalg %barstartalg%" /;
$if set barepcomp      put "barepcomp %barepcomp%" /;
$if set barcolnz       put "barcolnz %barcolnz%" /;
$if set solutiontype   put "solutiontype %solutiontype%" /;
$if set epgap          put "epgap %epgap%" /;

$if set datacheck      put "datacheck %datacheck%" /;
$if set iis            put "iis %iis%" /;
$if set quality        put "quality %quality%" /;

$if set randomseed     put "randomseed %randomseed%" /;
$if set cpumask        put "cpumask %cpumask%" /;
putclose;
$endif.solver


$iftheni.solver %solver%==gurobi
file opt / "%gams.optdir%gurobi.opt" /;
put opt;
$ife %names%=0         put "names 0" /;
$ife %rerun%=1         put "rerun 1" /;

$if set gurobimethod   put "method %gurobimethod%" /;
$if set threads        put "threads %threads%" /;
$if set barorder       put "barorder %barorder%" /;
$ife %crossover%=0     put "crossover 0" /;
$if set barconvtol     put "barconvtol %barconvtol%" /;

$if set presolve       put "presolve %presolve%" /;
$if set predual        put "predual %predual%" /;
$if set aggfill        put "aggfill %aggfill%" /;
$if set scaleflag      put "scaleflag %scaleflag%" /;
$if set numericfocus   put "numericfocus %numericfocus%" /;
$if set barhomogeneous put "barhomogeneous %barhomogeneous%" /;
$if set GURO_PAR_BARDENSETHRESH put "readparams %gams.optdir%gurobi.prm" /;
$if set mipgap         put "mipgap %mipgap%" /;
$if set iis            put "iis %iis%" /;
putclose;

* Write separate file for hidden Gurobi option
$ifthen.bardense set GURO_PAR_BARDENSETHRESH
file prm / "%gams.optdir%gurobi.prm" /;
put prm;
put "GURO_PAR_BARDENSETHRESH %GURO_PAR_BARDENSETHRESH%" /;
putclose;
$endif.bardense
$endif.solver


$iftheni.solver %solver%==copt
file opt / "%gams.optdir%copt.opt" /;
put opt;
$if set lpmethod       put "lpmethod %lpmethod%" /;
$if set threads        put "threads %threads%" /;
$if set barorder       put "barorder %barorder%" /;
$ife %crossover%=0     put "crossover 0" /;
$if set relgap         put "relgap %relgap%" /;

$if set presolve       put "presolve %presolve%" /;
$if set scaling        put "scaling %scaling%" /;
$if set dualize        put "dualize %dualize%" /;
$if set barhomogeneous put "barhomogeneous %barhomogeneous%" /;
$ife %iis%>0           put "iis %iis%" /;
putclose;
$endif.solver


$iftheni.solver %solver%==xpress
file opt / "%gams.optdir%xpress.opt" /;
put opt;
$if set algorithm      put "algorithm %algorithm%" /;
$if set threads        put "threads %threads%" /;
$if set barOrder       put "barOrder %barOrder%" /;
$ife %crossover%=0     put "crossover 0" /;
$if set barGapStop     put "barGapStop %barGapStop%" /;

$if set presolve       put "presolve %presolve%" /;
$if set autoScaling    put "autoScaling %autoScaling%" /;
$if set dualize        put "dualize %dualize%" /;
$if set mipRelStop     put "mipRelStop %mipRelStop%" /;
$ife %rerun%=1         put "rerun 1" /;
putclose;
$endif.solver


$iftheni.solver %solver%==highs
file opt / "%gams.optdir%highs.opt" /;
put opt;
$if set highssolver    put "solver = %highssolver%" /;
$if set threads        put "threads %threads%" /;
$if set pdlp_scaling   put "pdlp_scaling %pdlp_scaling%" /;
$ife %crossover%=0     put "run_crossover = off" /;
put "parallel = on" /;

$ife %presolve%=0      put "presolve = off" /;
put "mip_feasibility_tolerance = %epgap%" /;

putclose;
$endif.solver


$iftheni.solver %solver%==mosek
file opt / "%gams.optdir%mosek.opt" /;
put opt;
$if set MSK_IPAR_OPTIMIZER           put "MSK_IPAR_OPTIMIZER %MSK_IPAR_OPTIMIZER%" /;
$if set MSK_IPAR_NUM_THREADS         put "MSK_IPAR_NUM_THREADS %threads%" /;
$ife %crossover%=0                   put "MSK_IPAR_INTPNT_BASIS MSK_BI_NEVER" /;

$if set MSK_IPAR_PRESOLVE_USE        put "MSK_IPAR_LOG_PRESOLVE 10" /;
$if set MSK_IPAR_PRESOLVE_USE        put "MSK_IPAR_PRESOLVE_USE %MSK_IPAR_PRESOLVE_USE%" /;
$if set MSK_IPAR_INTPNT_SCALING      put "MSK_IPAR_INTPNT_SCALING %MSK_IPAR_INTPNT_SCALING%" /;
$if set MSK_IPAR_INTPNT_SOLVE_FORM   put "MSK_IPAR_INTPNT_SOLVE_FORM %MSK_IPAR_INTPNT_SOLVE_FORM%" /;
$if set MSK_IPAR_INTPNT_ORDER_METHOD put "MSK_IPAR_INTPNT_ORDER_METHOD %MSK_IPAR_INTPNT_ORDER_METHOD%" /;
$if set MSK_IPAR_INTPNT_OFF_COL_TRH  put "MSK_IPAR_INTPNT_OFF_COL_TRH %MSK_IPAR_INTPNT_OFF_COL_TRH%" /;
$ife %iis%<>0                        put "MSK_IPAR_INFEAS_REPORT_AUTO MSK_ON" /;

$if set MSK_DPAR_INTPNT_TOL_REL_GAP  put "MSK_DPAR_INTPNT_TOL_REL_GAP %MSK_DPAR_INTPNT_TOL_REL_GAP%" /;
$if set MSK_DPAR_MIO_TOL_REL_GAP     put "MSK_DPAR_MIO_TOL_REL_GAP %MSK_DPAR_MIO_TOL_REL_GAP%" /;
$if set MSK_DPAR_MIO_REL_GAP_CONST   put "MSK_DPAR_MIO_REL_GAP_CONST %MSK_DPAR_MIO_REL_GAP_CONST%" /;
$if set MSK_IPAR_MIO_ROOT_OPTIMIZER  put "MSK_IPAR_MIO_ROOT_OPTIMIZER %MSK_IPAR_MIO_ROOT_OPTIMIZER%" /;
putclose;
$endif.solver


$iftheni.solver %solver%==convert
file opt / "%gams.optdir%convert.opt" /;
put opt;
put "CplexLP %gams.optdir%%gams.filestem%.lp" /;
put "CplexMPS %gams.optdir%%gams.filestem%.mps" /;
put "Dict %gams.optdir%%gams.filestem%_dict.txt" /;
putclose;
$endif.solver


$iftheni.solver %solver%==scip
file opt / "%gams.optdir%scip.opt" /;
put opt;
put 'gams/interactive = "write prob remix.cip quit"' /;
putclose;
$endif.solver

$offVerbatim