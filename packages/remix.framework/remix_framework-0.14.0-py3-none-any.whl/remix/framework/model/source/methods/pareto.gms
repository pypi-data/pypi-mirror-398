* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

$onVerbatim
$iftheni.method %method%==pareto
$offVerbatim

$include "%sourcedir%/solver_options/defaults.gms"
$include "%sourcedir%/solver_options/write.gms"

variable pareto_objective;
equation Eq_pareto_obj;
equation Eq_pareto_limitObjective(accNodesModel,accYears,indicator);
Eq_pareto_limitObjective.m(accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"obj")
    = 0;

* ==== initial solution ====

loop ( optiframeToCalc,
    yearsSel(years) = no;
    yearsSel(years)$map_optiframe(optiframeToCalc,years) = yes;
    yearsToFix(years) = no;
    yearsToFix(years)$(years.val < smin(years_a$yearsSel(years_a), years_a.val)) = yes;
    accYearsSel(accYears) = no;
    accYearsSel("horizon") = yes;
    accYearsSel(accYears)$(sum(yearsSel$sameas(accYears,yearsSel), 1)) = yes;
    accYearsToFix(accYears) = no;
    accYearsToFix(accYears)$(sum(years$(sameas(years,accYears) and years.val < smin(years_a$yearsSel(years_a), years_a.val)), 1) > 0) = yes;
    timeModelSel(timeModel) = no;
    timeModelSel(timeModel)$timeModelToCalc(timeModel) = yes;
    nodesModelSel(nodesModel) = no;
    nodesModelSel(nodesModel)$nodesModelToCalc(nodesModel) = yes;

* Fix decision for years previously optimized in case of myopic or foresight
    converter_unitsDelta_upper(nodesModelToCalc,yearsToFix,converter_techs)
        $(sum(yearsToCalc$sameas(yearsToFix, yearsToCalc), 1))
        = sum(vintage, converter_unitsTotal.l(nodesModelToCalc,yearsToFix,converter_techs,vintage))
            - converter_capacityParam(nodesModelToCalc,yearsToFix,converter_techs,"unitsUpperLimit");
    converter_unitsDelta_upper(nodesModelToCalc,yearsToFix,converter_techs)
        $(converter_unitsDelta_upper(nodesModelToCalc,yearsToFix,converter_techs) < 0) = 0;

    converter_unitsDelta_lower(nodesModelToCalc,yearsToFix,converter_techs)
        $(sum(yearsToCalc$sameas(yearsToFix, yearsToCalc), 1))
        = converter_capacityParam(nodesModelToCalc,yearsToFix,converter_techs,"unitsLowerLimit")
            - sum(vintage, converter_unitsTotal.l(nodesModelToCalc,yearsToFix,converter_techs,vintage));
    converter_unitsDelta_lower(nodesModelToCalc,yearsToFix,converter_techs)
        $(converter_unitsDelta_lower(nodesModelToCalc,yearsToFix,converter_techs) < 0) = 0;

    converter_unitsDelta_decom(nodesModelToCalc,yearsSel,converter_techs,vintage)
        = converter_unitsDecom.lo(nodesModelToCalc,yearsSel,converter_techs,vintage)
            - sum(yearsToCalc$(ord(yearsToCalc) = 1 and sameas(yearsToCalc, yearsSel)),
                sum(years$sameas(years, yearsToCalc),
                    converter_unitsTotal.l(nodesModelToCalc,years-1,converter_techs,vintage)
                    $converter_usedTech(nodesModelToCalc,years-1,converter_techs,vintage)))
            - sum((yearsToCalc)$(ord(yearsToCalc) > 1 and sameas(yearsToCalc, yearsSel)),
                converter_unitsTotal.l(nodesModelToCalc,yearsToCalc-1,converter_techs,vintage)
                    $converter_usedTech(nodesModelToCalc,yearsToCalc-1,converter_techs,vintage));
    converter_unitsDelta_decom(nodesModelToCalc,yearsSel,converter_techs,vintage)
        $(converter_unitsDelta_decom(nodesModelToCalc,yearsSel,converter_techs,vintage) < 0) = 0;

    converter_unitsBuild.l(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        $converter_availTech(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        = converter_unitsBuild.l(nodesModelToCalc,yearsToFix,converter_techs,vintage)
            - converter_unitsDelta_upper(nodesModelToCalc,yearsToFix,converter_techs);

    converter_unitsDecom.l(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        $converter_usedTech(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        = converter_unitsDecom.l(nodesModelToCalc,yearsToFix,converter_techs,vintage)
            - converter_unitsDelta_lower(nodesModelToCalc,yearsToFix,converter_techs);

    converter_unitsBuild.l(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        $(converter_unitsBuild.l(nodesModelToCalc,yearsToFix,converter_techs,vintage) < 0) = 0;
    converter_unitsBuild.fx(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        = converter_unitsBuild.l(nodesModelToCalc,yearsToFix,converter_techs,vintage);
    converter_unitsDecom.l(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        $(converter_unitsDecom.l(nodesModelToCalc,yearsToFix,converter_techs,vintage) < 0) = 0;
    converter_unitsDecom.fx(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        = converter_unitsDecom.l(nodesModelToCalc,yearsToFix,converter_techs,vintage);
    converter_unitsTotal.fx(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        = converter_unitsTotal.l(nodesModelToCalc,yearsToFix,converter_techs,vintage);


    storage_unitsDelta_upper(nodesModelToCalc,yearsToFix,storage_techs)
        $(sum(yearsToCalc$sameas(yearsToFix, yearsToCalc), 1))
        = sum(vintage, storage_unitsTotal.l(nodesModelToCalc,yearsToFix,storage_techs,vintage))
            - storage_reservoirParam(nodesModelToCalc,yearsToFix,storage_techs,"unitsUpperLimit");
    storage_unitsDelta_upper(nodesModelToCalc,yearsToFix,storage_techs)
        $(storage_unitsDelta_upper(nodesModelToCalc,yearsToFix,storage_techs) < 0) = 0;

    storage_unitsDelta_lower(nodesModelToCalc,yearsToFix,storage_techs)
        $(sum(yearsToCalc$sameas(yearsToFix, yearsToCalc), 1))
        = storage_reservoirParam(nodesModelToCalc,yearsToFix,storage_techs,"unitsLowerLimit")
            - sum(vintage, storage_unitsTotal.l(nodesModelToCalc,yearsToFix,storage_techs,vintage));
    storage_unitsDelta_lower(nodesModelToCalc,yearsToFix,storage_techs)
        $(storage_unitsDelta_lower(nodesModelToCalc,yearsToFix,storage_techs) < 0) = 0;

    storage_unitsDelta_decom(nodesModelToCalc,yearsSel,storage_techs,vintage)
        = storage_unitsDecom.lo(nodesModelToCalc,yearsSel,storage_techs,vintage)
            - sum(yearsToCalc$(ord(yearsToCalc) = 1 and sameas(yearsToCalc, yearsSel)),
                sum(years$sameas(years, yearsToCalc),
                    storage_unitsTotal.l(nodesModelToCalc,years-1,storage_techs,vintage)
                    $storage_usedTech(nodesModelToCalc,years-1,storage_techs,vintage)))
            - sum((yearsToCalc)$(ord(yearsToCalc) > 1 and sameas(yearsToCalc, yearsSel)),
                storage_unitsTotal.l(nodesModelToCalc,yearsToCalc-1,storage_techs,vintage)
                    $storage_usedTech(nodesModelToCalc,yearsToCalc-1,storage_techs,vintage));
    storage_unitsDelta_decom(nodesModelToCalc,yearsSel,storage_techs,vintage)
        $(storage_unitsDelta_decom(nodesModelToCalc,yearsSel,storage_techs,vintage) < 0) = 0;

    storage_unitsBuild.l(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        $storage_availTech(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        = storage_unitsBuild.l(nodesModelToCalc,yearsToFix,storage_techs,vintage)
            - storage_unitsDelta_upper(nodesModelToCalc,yearsToFix,storage_techs);

    storage_unitsDecom.l(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        $storage_usedTech(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        = storage_unitsDecom.l(nodesModelToCalc,yearsToFix,storage_techs,vintage)
            - storage_unitsDelta_lower(nodesModelToCalc,yearsToFix,storage_techs);

    storage_unitsBuild.l(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        $(storage_unitsBuild.l(nodesModelToCalc,yearsToFix,storage_techs,vintage) < 0) = 0;
    storage_unitsBuild.fx(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        = storage_unitsBuild.l(nodesModelToCalc,yearsToFix,storage_techs,vintage);
    storage_unitsDecom.l(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        $(storage_unitsDecom.l(nodesModelToCalc,yearsToFix,storage_techs,vintage) < 0) = 0;
    storage_unitsDecom.fx(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        = storage_unitsDecom.l(nodesModelToCalc,yearsToFix,storage_techs,vintage);
    storage_unitsTotal.fx(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        = storage_unitsTotal.l(nodesModelToCalc,yearsToFix,storage_techs,vintage);


    transfer_linksDelta_upper(linksModelToCalc,yearsToFix,transfer_techs)
        $(sum(yearsToCalc$sameas(yearsToFix, yearsToCalc), 1))
        = sum(vintage, transfer_linksTotal.l(linksModelToCalc,yearsToFix,transfer_techs,vintage))
            - transfer_linksParam(linksModelToCalc,yearsToFix,transfer_techs,"linksUpperLimit");
    transfer_linksDelta_upper(linksModelToCalc,yearsToFix,transfer_techs)
        $(transfer_linksDelta_upper(linksModelToCalc,yearsToFix,transfer_techs) < 0) = 0;

    transfer_linksDelta_lower(linksModelToCalc,yearsToFix,transfer_techs)
        $(sum(yearsToCalc$sameas(yearsToFix, yearsToCalc), 1))
        = transfer_linksParam(linksModelToCalc,yearsToFix,transfer_techs,"linksLowerLimit")
            - sum(vintage, transfer_linksTotal.l(linksModelToCalc,yearsToFix,transfer_techs,vintage));
    transfer_linksDelta_lower(linksModelToCalc,yearsToFix,transfer_techs)
        $(transfer_linksDelta_lower(linksModelToCalc,yearsToFix,transfer_techs) < 0) = 0;

    transfer_linksDelta_decom(linksModelToCalc,yearsSel,transfer_techs,vintage)
        = transfer_linksDecom.lo(linksModelToCalc,yearsSel,transfer_techs,vintage)
            - sum(yearsToCalc$(ord(yearsToCalc) = 1 and sameas(yearsToCalc, yearsSel)),
                sum(years$sameas(years, yearsToCalc),
                    transfer_linksTotal.l(linksModelToCalc,years-1,transfer_techs,vintage)
                    $transfer_usedTech(linksModelToCalc,years-1,transfer_techs,vintage)))
            - sum((yearsToCalc)$(ord(yearsToCalc) > 1 and sameas(yearsToCalc, yearsSel)),
                transfer_linksTotal.l(linksModelToCalc,yearsToCalc-1,transfer_techs,vintage)
                    $transfer_usedTech(linksModelToCalc,yearsToCalc-1,transfer_techs,vintage));
    transfer_linksDelta_decom(linksModelToCalc,yearsSel,transfer_techs,vintage)
        $(transfer_linksDelta_decom(linksModelToCalc,yearsSel,transfer_techs,vintage) < 0) = 0;

    transfer_linksBuild.l(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        $transfer_availTech(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        = transfer_linksBuild.l(linksModelToCalc,yearsToFix,transfer_techs,vintage)
            - transfer_linksDelta_upper(linksModelToCalc,yearsToFix,transfer_techs);

    transfer_linksDecom.l(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        $transfer_usedTech(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        = transfer_linksDecom.l(linksModelToCalc,yearsToFix,transfer_techs,vintage)
            - transfer_linksDelta_lower(linksModelToCalc,yearsToFix,transfer_techs);

    transfer_linksBuild.l(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        $(transfer_linksBuild.l(linksModelToCalc,yearsToFix,transfer_techs,vintage) < 0) = 0;
    transfer_linksBuild.fx(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        = transfer_linksBuild.l(linksModelToCalc,yearsToFix,transfer_techs,vintage);
    transfer_linksDecom.l(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        $(transfer_linksDecom.l(linksModelToCalc,yearsToFix,transfer_techs,vintage) < 0) = 0;
    transfer_linksDecom.fx(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        = transfer_linksDecom.l(linksModelToCalc,yearsToFix,transfer_techs,vintage);
    transfer_linksTotal.fx(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        = transfer_linksTotal.l(linksModelToCalc,yearsToFix,transfer_techs,vintage);

    accounting_indicator.fx(accNodesModel,accYearsToFix,indicator)
        = accounting_indicator.l(accNodesModel,accYearsToFix,indicator);

* Optimize and log values
$onVerbatim
    remix.holdFixed = %holdfixed%;
$offVerbatim

put_utility 'log' / 'Running base optimization ';

    solve remix minimizing accounting_objective using MIP;
    put_utility 'log' / 'Model status ' remix.modelstat:0:0;
    put_utility 'log' / 'Objective value ' accounting_objective.l:0:3;

);

$include "%sourcedir%/postcalc/definition.gms"


* ==== modify the model and solve for pareto points ====

* After writing the initial solution to pareto0 reset the active set and run the pareto loop
pareto_act(pareto) = no;


parameter pareto_points(pareto);
$onVerbatim
pareto_points(pareto) = (%paretofactor% - 1) / %paretopoints% * (ord(pareto) - 1);
$offVerbatim

Eq_pareto_limitObjective(accNodesModel,accYears,indicator)
    $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"obj") <> 0 )
    ..
    (-1 * accounting_indicatorBounds(accNodesModel,accYears,indicator,"obj"))
        *
$include "%sourcedir%/accounting/inc_accnodes.gms"
    =l=
    accounting_objective.l * sum(pareto_act, 1 + pareto_points(pareto_act));

Eq_pareto_obj
    ..
    pareto_objective
    =e=
    sum ((accNodesModel,accYears,indicator)
            $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"pareto") <> 0 ),
        (-1 * accounting_indicatorBounds(accNodesModel,accYears,indicator,"pareto"))
        *
$include "%sourcedir%/accounting/inc_accnodes.gms"
    );

model remix_pareto
    /
    remix
    - Eq_accounting_objective
    + Eq_pareto_limitObjective
    + Eq_pareto_obj
    /;

$set modeltype MIP

$onVerbatim
option %modeltype% = %solver%;

remix_pareto.holdFixed = %holdfixed%;
$offVerbatim
remix_pareto.optfile = 1;

loop(pareto$(ord(pareto) > 1),
    pareto_act(pareto) = yes;

put_utility 'log' / 'Running pareto point ' (ord(pareto)-1):0:0 ;

$onVerbatim
    solve remix_pareto minimizing pareto_objective using %modeltype%;
$offVerbatim

$include "%sourcedir%/postcalc/definition.gms"
    pareto_act(pareto) = no;
);

$include "%sourcedir%/postcalc/writegdx.gms"
$setglobal run_postcalc 0

$onVerbatim
$endif.method
$offVerbatim
