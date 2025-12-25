* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

$onVerbatim
$iftheni.method %method%==mga
$offVerbatim

$include "%sourcedir%/solver_options/defaults.gms"
$include "%sourcedir%/solver_options/write.gms"

variable mga_objective;

positive variable mga_dist(mga,accNodesModel,accYears,indicator);
positive variable mga_dist_pos(mga,accNodesModel,accYears,indicator);
positive variable mga_dist_neg(mga,accNodesModel,accYears,indicator);
equation Eq_mga_obj;
equation Eq_mga_hyperray(accNodesModel,accYears,indicator);
equation Eq_mga_limitObjective(accNodesModel,accYears,indicator);
Eq_mga_limitObjective.m(accNodesModel,accYears,indicator)
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
mga_comp(mga)$mga_act(mga) = yes;
mga_act(mga) = no;


* ==== modify the model and solve for alternatives ====

parameter mga_indicatorPoints(mga,accNodesModel,accYears,indicator);
mga_indicatorPoints(mga,accNodesModel,accYears,indicator)
    $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
        and ord(mga) = 1)
    = 
$onDotL
$include "%sourcedir%/accounting/inc_accnodes.gms"
$offDotL
    ;

Eq_mga_limitObjective(accNodesModel,accYears,indicator)
    $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"obj") <> 0 )
    ..
    (-1 * accounting_indicatorBounds(accNodesModel,accYears,indicator,"obj"))
        *
$include "%sourcedir%/accounting/inc_accnodes.gms"
    =l=
$onVerbatim
    accounting_objective.l * %mgafactor%;

$iftheni.mgamethod %mgamethod%==linear
* LINEAR FORMULATION, PUSHES TOWARDS HIGHER INDICATORS
$offVerbatim

Eq_mga_obj
    ..
    mga_objective
    =e=
    sum((mga_comp,accNodesModel,accYears,indicator)
            $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga"),
        mga_dist(mga_comp,accNodesModel,accYears,indicator))
    / sum((mga_comp,accNodesModel,accYears,indicator)
            $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga"),
        1);

equation Eq_mga_distance(mga,accNodesModel,accYears,indicator);
Eq_mga_distance(mga_comp,accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
    ..
    mga_dist(mga_comp,accNodesModel,accYears,indicator)
    =e=
    ( 
$include "%sourcedir%/accounting/inc_accnodes.gms"
    )
    / mga_indicatorPoints(mga_comp,accNodesModel,accYears,indicator)

model remix_mga
    /
    remix
    - Eq_accounting_objective
    + Eq_mga_limitObjective
    + Eq_mga_distance
    + Eq_mga_obj
    /;

$set modeltype LP

$onVerbatim
$elseifi.mgamethod %mgamethod%==binary
$offVerbatim
* BINARY FORMULATION, DISTANCE AS ABSOLUTE VALUE
binary variable mga_dist_bool(mga,accNodesModel,accYears,indicator);

Eq_mga_obj
    ..
    mga_objective
    =e=
    sum((mga_comp,accNodesModel,accYears,indicator)
            $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga"),
        mga_dist_pos(mga_comp,accNodesModel,accYears,indicator)
        + mga_dist_neg(mga_comp,accNodesModel,accYears,indicator))
    / sum((mga_comp,accNodesModel,accYears,indicator)
            $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga"),
        1);

equation Eq_mga_bool_pos(mga,accNodesModel,accYears,indicator);
Eq_mga_bool_pos(mga_comp,accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
    ..
    mga_dist_pos(mga_comp,accNodesModel,accYears,indicator)
    =l=
    10 * mga_dist_bool(mga_comp,accNodesModel,accYears,indicator)

equation Eq_mga_bool_neg(mga,accNodesModel,accYears,indicator);
Eq_mga_bool_neg(mga_comp,accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
    ..
    mga_dist_neg(mga_comp,accNodesModel,accYears,indicator)
    =l=
    10 * (1 - mga_dist_bool(mga_comp,accNodesModel,accYears,indicator))

equation Eq_mga_distance(mga,accNodesModel,accYears,indicator);
Eq_mga_distance(mga_comp,accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
    ..
    mga_dist_pos(mga_comp,accNodesModel,accYears,indicator)
    - mga_dist_neg(mga_comp,accNodesModel,accYears,indicator)
    =e=
    ( accounting_indicator(accNodesModel,accYears,indicator))
    / mga_indicatorPoints(mga_comp,accNodesModel,accYears,indicator)

model remix_mga
    /
    remix
    - Eq_accounting_objective
    + Eq_mga_limitObjective
    + Eq_mga_bool_pos
    + Eq_mga_bool_neg
    + Eq_mga_distance
    + Eq_mga_obj
    /;

$set modeltype MIP

$onVerbatim
$elseifi.mgamethod %mgamethod%==quadratic
$offVerbatim
* QUADRATIC FORMULATION, DISTANCE AS SQUARE VALUE

mga_indicatorPoints(mga,accNodesModel,accYears,indicator)
    $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
        and ord(mga) = 1)
    = accounting_indicator.l(accNodesModel,accYears,indicator);

Eq_mga_obj
    ..
    mga_objective
    =e=
    sum((mga_comp,accNodesModel,accYears,indicator)
            $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga"),
        mga_dist_pos(mga_comp,accNodesModel,accYears,indicator)
        + mga_dist_neg(mga_comp,accNodesModel,accYears,indicator))
    / sum((mga_comp,indicator)
            $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga"),
        1);

equation Eq_mga_bool_pos(mga,accNodesModel,accYears,indicator);
Eq_mga_bool_pos(mga_comp,accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
    ..
    mga_dist_pos(mga_comp,accNodesModel,accYears,indicator)
    =l=
    10 * mga_dist_bool(mga_comp,accNodesModel,accYears,indicator)

equation Eq_mga_bool_neg(mga,accNodesModel,accYears,indicator);
Eq_mga_bool_neg(mga_comp,accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
    ..
    mga_dist_neg(mga_comp,accNodesModel,accYears,indicator)
    =l=
    10 * (1 - mga_dist_bool(mga_comp,accNodesModel,accYears,indicator))

equation Eq_mga_distance(mga,accNodesModel,accYears,indicator);
Eq_mga_distance(mga_comp,accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
    ..
    mga_dist_pos(mga_comp,accNodesModel,accYears,indicator)
    - mga_dist_neg(mga_comp,accNodesModel,accYears,indicator)
    =e=
    ( accounting_indicator(accNodesModel,accYears,indicator))
    / mga_indicatorPoints(mga_comp,accNodesModel,accYears,indicator)

model remix_mga
    /
    remix
    - Eq_accounting_objective
    + Eq_mga_limitObjective
    + Eq_mga_bool_pos
    + Eq_mga_bool_neg
    + Eq_mga_distance
    + Eq_mga_obj
    /;

$set modeltype QCP

$onVerbatim
$elseifi.mgamethod %mgamethod%==hypersphere
$offVerbatim
set mga_indicators(indicator);
mga_indicators(indicator)
    $sum((accNodesModel,accYears)$accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga"), 1)
 = yes;

parameter mga_weights(mga, indicator);

embeddedCode Python:
    try:
        from remix.framework.tools.mga import uniform_hypersphere
    except ImportError:
        from sys import path
        from pathlib import Path
        model_dir = Path(r'%sourcedir% '.strip()).parents[3].as_posix()
        if model_dir not in path:
            path.append(model_dir)
        from remix.framework.tools.mga import uniform_hypersphere

    points = list(gams.get("mga"))
    indicators = list(gams.get("mga_indicators"))

    data = [[round(i,4) for i in j] for j in uniform_hypersphere(len(indicators), len(points))]
    weights = [((p,m), data[i][j]) for i, p in enumerate(points) for j, m in enumerate(indicators)]

    gams.set("mga_weights", weights)
endEmbeddedCode mga_weights

Eq_mga_hyperray(accNodesModel,accYears,indicator)
    $accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga")
    ..
$include "%sourcedir%/accounting/inc_accnodes.gms"
    =e=
    mga_indicatorPoints("mga0",accNodesModel,accYears,indicator)
    + sum(mga_act, mga_objective * mga_weights(mga_act,indicator))
    ;

model remix_mga
    /
    remix
    - Eq_accounting_objective
    + Eq_mga_limitObjective
    + Eq_mga_hyperray
    /;

$set modeltype MIP
$onVerbatim
$endif.mgamethod


* run the loop for the configured MGA method

option %modeltype% = %solver%;

remix_mga.holdFixed = %holdfixed%;
remix_mga.optfile = 1;
$offVerbatim

loop(mga$(ord(mga) > 1),
    mga_act(mga) = yes;

put_utility 'log' / 'Running MGA point ' (ord(mga)-1):0:0 ;

$onVerbatim
    solve remix_mga maximizing mga_objective using %modeltype%;
$offVerbatim

    mga_indicatorPoints(mga,accNodesModel,accYears,indicator)
    $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"mga"))
    = accounting_indicator.l(accNodesModel,accYears,indicator);

$include "%sourcedir%/postcalc/definition.gms"
    mga_comp(mga) = yes;
    mga_act(mga) = no;
);

$include "%sourcedir%/postcalc/writegdx.gms"
$setglobal run_postcalc 0

$onVerbatim
$endif.method
$offVerbatim
