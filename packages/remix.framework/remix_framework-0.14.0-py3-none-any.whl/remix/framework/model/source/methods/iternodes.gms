* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

$onVerbatim
$iftheni.method %method%==iternodes

* ==== global options ====
$if not set submits    $set submits           8

$offVerbatim

$include "%sourcedir%/solver_options/defaults.gms"
$include "%sourcedir%/solver_options/write.gms"

* ==== solve the problem ====

* mapping from optimization frame to years
parameter h(nodesModel);
h(nodesModel) = 0;
parameter sol(nodesModel);
sol(nodesModel) = 0;
scalar submit;
submit = 0;

remix.solveLink = 3;

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

* Fix decision for years previously optimized in case of myopic or foresight
    converter_unitsBuild.fx(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        = converter_unitsBuild.l(nodesModelToCalc,yearsToFix,converter_techs,vintage);
    converter_unitsDecom.fx(nodesModelToCalc,yearsToFix,converter_techs,vintage)
        = converter_unitsDecom.l(nodesModelToCalc,yearsToFix,converter_techs,vintage);
    
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

    storage_unitsBuild.fx(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        = storage_unitsBuild.l(nodesModelToCalc,yearsToFix,storage_techs,vintage);
    storage_unitsDecom.fx(nodesModelToCalc,yearsToFix,storage_techs,vintage)
        = storage_unitsDecom.l(nodesModelToCalc,yearsToFix,storage_techs,vintage);
    
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

    transfer_linksBuild.fx(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        = transfer_linksBuild.l(linksModelToCalc,yearsToFix,transfer_techs,vintage);
    transfer_linksDecom.fx(linksModelToCalc,yearsToFix,transfer_techs,vintage)
        = transfer_linksDecom.l(linksModelToCalc,yearsToFix,transfer_techs,vintage);
    
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

    accounting_indicator.fx(accNodesModel,accYearsToFix,indicator)
        = accounting_indicator.l(accNodesModel,accYearsToFix,indicator);

    repeat
        submit = 0;
        loop(nodesModel$(nodesModelToCalc(nodesModel) and h(nodesModel) = 0 and sol(nodesModel) = 0),
$onVerbatim
            if ((sum(nodesModel_a$h(nodesModel_a), 1) < %submits% and submit < 2),
                nodesModelSel(nodesModel)$nodesModelToCalc(nodesModel) = yes;

                solve remix minimizing accounting_objective using mip;

                nodesModelSel(nodesModel) = no;
                h(nodesModel) = remix.handle;
                submit = submit + 1;
            );
$offVerbatim
        );

        loop(nodesModel$handleCollect(h(nodesModel)),
            display$handleDelete(h(nodesModel)) 'trouble deleting handles' ;
            h(nodesModel) = 0;
            sol(nodesModel) = 1;
        );
    until sum(nodesModel_a$sol(nodesModel_a), 1) = card(nodesModelToCalc);
);

$onVerbatim
$endif.method
$offVerbatim
