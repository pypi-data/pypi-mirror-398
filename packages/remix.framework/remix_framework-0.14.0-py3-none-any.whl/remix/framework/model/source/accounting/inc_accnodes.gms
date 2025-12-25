* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

* == variable indicators ==
    sum((accNodesModel_a,accYears_a,indicator_a)
        $(compoundIndicatorsExt(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a,accNodesModel_a,accYears_a,indicator_a)
            and variableIndicators(accNodesModel_a,accYears_a,indicator_a)),
        compoundIndicatorsExt(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a,accNodesModel_a,accYears_a,indicator_a)
        * accounting_indicator(accNodesModel_a,accYears_a,indicator_a)
        )

* == converters ==
    + sum ((accNodesModel_a,nodesModelSel,accYears_a,yearsSel,indicator_a)
            $( compoundIndicators(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a)
                and sameas(nodesModelSel,accNodesModel_a) and sameas(yearsSel,accYears_a)),
        compoundIndicators(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a)
        *
        ( sum ((converter_techs,vintage)
                    $(converter_availTech(nodesModelSel,yearsSel,converter_techs,vintage)
                        and accounting_converterUnits(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"useAnnuity") = 0),
            converter_unitsBuild(nodesModelSel,yearsSel,converter_techs,vintage)
            * accounting_converterUnits(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"perUnitBuild")
            )

        + sum ((years_a,converter_techs,vintage)
                    $(converter_availTech(nodesModelSel,years_a,converter_techs,vintage)
                        and years_a.val < sum(yearsToCalc_a$(ord(yearsToCalc_a)=1), yearsToCalc_a.val)
                        and accounting_converterUnits(indicator_a,nodesModelSel,years_a,converter_techs,vintage,"useAnnuity") = 1
                        and years_a.val + accounting_converterUnits(indicator_a,nodesModelSel,years_a,converter_techs,vintage,"amorTime") > yearsSel.val
                        and years_a.val <= yearsSel.val ),
            converter_unitsBuild(nodesModelSel,years_a,converter_techs,vintage)
            * accounting_converterUnits(indicator_a,nodesModelSel,years_a,converter_techs,vintage,"perUnitBuild")
            * accounting_annuityFactor_converter(indicator_a,nodesModelSel,years_a,converter_techs,vintage)
            )

        + sum ((yearsToCalc,converter_techs,vintage)
                    $(converter_availTech(nodesModelSel,yearsToCalc,converter_techs,vintage)
                        and yearsToCalc.val >= sum(yearsToCalc_a$(ord(yearsToCalc_a)=1), yearsToCalc_a.val)
                        and accounting_converterUnits(indicator_a,nodesModelSel,yearsToCalc,converter_techs,vintage,"useAnnuity") = 1
                        and yearsToCalc.val + accounting_converterUnits(indicator_a,nodesModelSel,yearsToCalc,converter_techs,vintage,"amorTime") > yearsSel.val
                        and yearsToCalc.val <= yearsSel.val ),
            converter_unitsBuild(nodesModelSel,yearsToCalc,converter_techs,vintage)
            * accounting_converterUnits(indicator_a,nodesModelSel,yearsToCalc,converter_techs,vintage,"perUnitBuild")
            * accounting_annuityFactor_converter(indicator_a,nodesModelSel,yearsToCalc,converter_techs,vintage)
            )

        + sum ((converter_techs,vintage)
                    $(converter_decomTech(nodesModelSel,yearsSel,converter_techs,vintage)
                        and converter_techParam(converter_techs,vintage,"freeDecom")),
            converter_unitsDecom(nodesModelSel,yearsSel,converter_techs,vintage)
            * accounting_converterUnits(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"perUnitDecom"))

        + sum ((converter_techs,vintage)
                    $converter_usedTech(nodesModelSel,yearsSel,converter_techs,vintage),
            + converter_unitsTotal(nodesModelSel,yearsSel,converter_techs,vintage)
            * accounting_converterUnits(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"perUnitTotal"))

        + sum ((timeModelSel,converter_techs,vintage,activity)
                    $converter_usedTechAct(nodesModelSel,yearsSel,converter_techs,vintage,activity),
            converter_activity(timeModelSel,nodesModelSel,yearsSel,converter_techs,vintage,activity)
            * timeLength(timeModelSel)
            * accounting_converterActivity(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,activity,"perActivity") )
        / timefrac

        + sum ((timeModelSel,converter_techs,vintage)
                    $converter_usedTech(nodesModelSel,yearsSel,converter_techs,vintage),
            converter_unitStartups(timeModelSel,nodesModelSel,yearsSel,converter_techs,vintage)
            * accounting_converterStartup(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"perStartup") )
        / timefrac

        + sum ((timeModelSel,converter_techs,vintage)
                    $converter_usedTech(nodesModelSel,yearsSel,converter_techs,vintage),
            converter_rampPos(timeModelSel,nodesModelSel,yearsSel,converter_techs,vintage)
            * (accounting_converterStartup(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"perRamp")
               + accounting_converterStartup(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"perRampPos"))

            + converter_rampNeg(timeModelSel,nodesModelSel,yearsSel,converter_techs,vintage)
            * (accounting_converterStartup(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"perRamp")
               + accounting_converterStartup(indicator_a,nodesModelSel,yearsSel,converter_techs,vintage,"perRampNeg")))
        / timefrac
        )
    )

* == storage ==
    + sum ((accNodesModel_a,nodesModelSel,accYears_a,yearsSel,indicator_a)
            $( compoundIndicators(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a)
                and sameas(nodesModelSel,accNodesModel_a) and sameas(yearsSel,accYears_a)),
        compoundIndicators(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a)
        *
        ( sum ((storage_techs,vintage)
                    $(storage_availTech(nodesModelSel,yearsSel,storage_techs,vintage)
                        and accounting_storageUnits(indicator_a,nodesModelSel,yearsSel,storage_techs,vintage,"useAnnuity") = 0),
            storage_unitsBuild(nodesModelSel,yearsSel,storage_techs,vintage)
            * accounting_storageUnits(indicator_a,nodesModelSel,yearsSel,storage_techs,vintage,"perUnitBuild")
            )

        + sum ((years_a,storage_techs,vintage)
                    $(storage_availTech(nodesModelSel,years_a,storage_techs,vintage)
                        and years_a.val < sum(yearsToCalc_a$(ord(yearsToCalc_a)=1), yearsToCalc_a.val)
                        and accounting_storageUnits(indicator_a,nodesModelSel,years_a,storage_techs,vintage,"useAnnuity") = 1
                        and years_a.val + accounting_storageUnits(indicator_a,nodesModelSel,years_a,storage_techs,vintage,"amorTime") > yearsSel.val
                        and years_a.val <= yearsSel.val ),
            storage_unitsBuild(nodesModelSel,years_a,storage_techs,vintage)
            * accounting_storageUnits(indicator_a,nodesModelSel,years_a,storage_techs,vintage,"perUnitBuild")
            * accounting_annuityFactor_storage(indicator_a,nodesModelSel,years_a,storage_techs,vintage)
            )

        + sum ((yearsToCalc,storage_techs,vintage)
                    $(storage_availTech(nodesModelSel,yearsToCalc,storage_techs,vintage)
                        and yearsToCalc.val >= sum(yearsToCalc_a$(ord(yearsToCalc_a)=1), yearsToCalc_a.val)
                        and accounting_storageUnits(indicator_a,nodesModelSel,yearsToCalc,storage_techs,vintage,"useAnnuity") = 1
                        and yearsToCalc.val + accounting_storageUnits(indicator_a,nodesModelSel,yearsToCalc,storage_techs,vintage,"amorTime") > yearsSel.val
                        and yearsToCalc.val <= yearsSel.val ),
            storage_unitsBuild(nodesModelSel,yearsToCalc,storage_techs,vintage)
            * accounting_storageUnits(indicator_a,nodesModelSel,yearsToCalc,storage_techs,vintage,"perUnitBuild")
            * accounting_annuityFactor_storage(indicator_a,nodesModelSel,yearsToCalc,storage_techs,vintage)
            )

        + sum ((storage_techs,vintage)
                    $(storage_decomTech(nodesModelSel,yearsSel,storage_techs,vintage)
                        and storage_techParam(storage_techs,vintage,"freeDecom")),
            storage_unitsDecom(nodesModelSel,yearsSel,storage_techs,vintage)
            * accounting_storageUnits(indicator_a,nodesModelSel,yearsSel,storage_techs,vintage,"perUnitDecom"))

        + sum ((storage_techs,vintage)
                    $storage_usedTech(nodesModelSel,yearsSel,storage_techs,vintage),
            + storage_unitsTotal(nodesModelSel,yearsSel,storage_techs,vintage)
            * accounting_storageUnits(indicator_a,nodesModelSel,yearsSel,storage_techs,vintage,"perUnitTotal"))
        )
    )


* == transfer ==
    + sum ((accNodesModel_a,nodesModelSel,accYears_a,yearsSel,indicator_a)
            $( compoundIndicators(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a)
                and sameas(nodesModelSel,accNodesModel_a) and sameas(yearsSel,accYears_a)),
        compoundIndicators(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a)
        *
        ( sum ((linksModelToCalc,transfer_techs,vintage)
                    $(transfer_availTech(linksModelToCalc,yearsSel,transfer_techs,vintage)
                        and transfer_incidenceModel(nodesModelSel,linksModelToCalc) <> 0
                        and accounting_transferLinks(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,"useAnnuity") = 0),
            0.5
            * transfer_linksBuild(linksModelToCalc,yearsSel,transfer_techs,vintage)
            * accounting_transferLinks(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,"perLinkBuild") )

        + sum ((linksModelToCalc,years_a,transfer_techs,vintage)
                    $(transfer_availTech(linksModelToCalc,years_a,transfer_techs,vintage)
                        and years_a.val < sum(yearsToCalc_a$(ord(yearsToCalc_a)=1), yearsToCalc_a.val)
                        and transfer_incidenceModel(nodesModelSel,linksModelToCalc) <> 0
                        and accounting_transferLinks(indicator_a,linksModelToCalc,years_a,transfer_techs,vintage,"useAnnuity") = 1
                        and years_a.val + accounting_transferLinks(indicator_a,linksModelToCalc,years_a,transfer_techs,vintage,"amorTime") > yearsSel.val
                        and years_a.val <= yearsSel.val ),
            0.5
            * transfer_linksBuild(linksModelToCalc,years_a,transfer_techs,vintage)
            * accounting_transferLinks(indicator_a,linksModelToCalc,years_a,transfer_techs,vintage,"perLinkBuild")
            * accounting_annuityFactor_transferLink(indicator_a,linksModelToCalc,years_a,transfer_techs,vintage) )

        + sum ((linksModelToCalc,yearsToCalc,transfer_techs,vintage)
                    $(transfer_availTech(linksModelToCalc,yearsToCalc,transfer_techs,vintage)
                        and yearsToCalc.val >= sum(yearsToCalc_a$(ord(yearsToCalc_a)=1), yearsToCalc_a.val)
                        and transfer_incidenceModel(nodesModelSel,linksModelToCalc) <> 0
                        and accounting_transferLinks(indicator_a,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"useAnnuity") = 1
                        and yearsToCalc.val + accounting_transferLinks(indicator_a,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"amorTime") > yearsSel.val
                        and yearsToCalc.val <= yearsSel.val ),
            0.5
            * transfer_linksBuild(linksModelToCalc,yearsToCalc,transfer_techs,vintage)
            * accounting_transferLinks(indicator_a,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"perLinkBuild")
            * accounting_annuityFactor_transferLink(indicator_a,linksModelToCalc,yearsToCalc,transfer_techs,vintage) )

        + sum ((linksModelToCalc,transfer_techs,vintage,link_types)
                    $(transfer_availTech(linksModelToCalc,yearsSel,transfer_techs,vintage)
                        and transfer_incidenceModel(nodesModelSel,linksModelToCalc) <> 0
                        and accounting_transferPerLength(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"useAnnuity") = 0 ),
            0.5
            * transfer_linksBuild(linksModelToCalc,yearsSel,transfer_techs,vintage)
            * transfer_lengthParam(linksModelToCalc,link_types,"length")
            * accounting_transferPerLength(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perLengthBuild") )

        + sum ((linksModelToCalc,years_a,transfer_techs,vintage,link_types)
                    $(transfer_availTech(linksModelToCalc,years_a,transfer_techs,vintage)
                        and years_a.val < sum(yearsToCalc_a$(ord(yearsToCalc_a)=1), yearsToCalc_a.val)
                        and transfer_incidenceModel(nodesModelSel,linksModelToCalc) <> 0
                        and accounting_transferPerLength(indicator_a,linksModelToCalc,years_a,transfer_techs,vintage,link_types,"useAnnuity") = 1
                        and years_a.val + accounting_transferPerLength(indicator_a,linksModelToCalc,years_a,transfer_techs,vintage,link_types,"amorTime") > yearsSel.val
                        and years_a.val <= yearsSel.val ),
            0.5
            * transfer_linksBuild(linksModelToCalc,years_a,transfer_techs,vintage)
            * transfer_lengthParam(linksModelToCalc,link_types,"length")
            * accounting_transferPerLength(indicator_a,linksModelToCalc,years_a,transfer_techs,vintage,link_types,"perLengthBuild")
            * accounting_annuityFactor_transferPerLength(indicator_a,linksModelToCalc,years_a,transfer_techs,vintage,link_types) )

        + sum ((linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types)
                    $(transfer_availTech(linksModelToCalc,yearsToCalc,transfer_techs,vintage)
                        and yearsToCalc.val >= sum(yearsToCalc_a$(ord(yearsToCalc_a)=1), yearsToCalc_a.val)
                        and transfer_incidenceModel(nodesModelSel,linksModelToCalc) <> 0
                        and accounting_transferPerLength(indicator_a,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"useAnnuity") = 1
                        and yearsToCalc.val + accounting_transferPerLength(indicator_a,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"amorTime") > yearsSel.val
                        and yearsToCalc.val <= yearsSel.val ),
            0.5
            * transfer_linksBuild(linksModelToCalc,yearsToCalc,transfer_techs,vintage)
            * transfer_lengthParam(linksModelToCalc,link_types,"length")
            * accounting_transferPerLength(indicator_a,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"perLengthBuild")
            * accounting_annuityFactor_transferPerLength(indicator_a,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types) )

        + sum ((linksModelToCalc,transfer_techs,vintage)
                    $(transfer_decomTech(linksModelToCalc,yearsSel,transfer_techs,vintage)
                        and transfer_incidenceModel(nodesModelSel,linksModelToCalc) <> 0
                        and transfer_techParam(transfer_techs,vintage,'freeDecom')),
            0.5
            * transfer_linksDecom(linksModelToCalc,yearsSel,transfer_techs,vintage)
            * accounting_transferLinks(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,"perLinkDecom")

            + 0.5
            * sum (link_types,
                transfer_linksDecom(linksModelToCalc,yearsSel,transfer_techs,vintage)
                * transfer_lengthParam(linksModelToCalc,link_types,"length")
                * accounting_transferPerLength(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perLengthDecom")
            ) )

        + sum ((linksModelToCalc,transfer_techs,vintage)
                    $(transfer_usedTech(linksModelToCalc,yearsSel,transfer_techs,vintage)
                        and transfer_incidenceModel(nodesModelSel,linksModelToCalc) <> 0 ),
            0.5
            * transfer_linksTotal(linksModelToCalc,yearsSel,transfer_techs,vintage)
            * accounting_transferLinks(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,"perLinkTotal")

            + 0.5
            * sum (link_types,
                transfer_linksTotal(linksModelToCalc,yearsSel,transfer_techs,vintage)
                * transfer_lengthParam(linksModelToCalc,link_types,"length")
                * accounting_transferPerLength(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perLengthTotal"))

            + 0.5
            * sum (timeModelSel,
                transfer_flowAlong(timeModelSel,linksModelToCalc,yearsSel,transfer_techs,vintage)
                * timeLength(timeModelSel)
                * ( accounting_transferLinks(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,"perFlow")
                    + accounting_transferLinks(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,"perFlowAlong"))

                + transfer_flowAgainst(timeModelSel,linksModelToCalc,yearsSel,transfer_techs,vintage)
                * timeLength(timeModelSel)
                * ( accounting_transferLinks(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,"perFlow")
                    + accounting_transferLinks(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,"perFlowAgainst")))
                / timefrac

            + 0.5
            * sum ((timeModelSel, link_types),
                transfer_flowAlong(timeModelSel,linksModelToCalc,yearsSel,transfer_techs,vintage)
                * timeLength(timeModelSel)
                * transfer_lengthParam(linksModelToCalc,link_types,"length")
                * (accounting_transferPerLength(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perFlow")
                    + accounting_transferPerLength(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perFlowAlong"))

                + transfer_flowAgainst(timeModelSel,linksModelToCalc,yearsSel,transfer_techs,vintage)
                * timeLength(timeModelSel)
                * transfer_lengthParam(linksModelToCalc,link_types,"length")
                * (accounting_transferPerLength(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perFlow")
                    + accounting_transferPerLength(indicator_a,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perFlowAgainst")))
                / timefrac
            )
        )
    )


* == sources / sinks ==
    + sum ((accNodesModel_a,nodesModelSel,accYears_a,yearsSel,indicator_a)
            $( compoundIndicators(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a)
                and sameas(nodesModelSel,accNodesModel_a) and sameas(yearsSel,accYears_a)),
        compoundIndicators(accNodesModel,accYears,indicator,accNodesModel_a,accYears_a,indicator_a)
        *
        sum ((timeModelSel,sourcesink_techs,commodity)
                $sourcesink_enabled(nodesModelSel,yearsSel,sourcesink_techs,commodity),
            sourcesink_flow(timeModelSel,nodesModelSel,yearsSel,sourcesink_techs,commodity)
            * timeLength(timeModelSel)
            * accounting_sourcesinkFlow(indicator_a,nodesModelSel,yearsSel,sourcesink_techs,commodity,"perFlow") )
        / timefrac
    )
