* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

    sum ((transfer_techs,vintage)
                $(transfer_availTech(linksModelToCalc,yearsSel,transfer_techs,vintage)
                    and accounting_transferLinks(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,"useAnnuity") = 0),
        transfer_linksBuild(linksModelToCalc,yearsSel,transfer_techs,vintage)
        * accounting_transferLinks(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,"perLinkBuild") )

    + sum ((years_a,transfer_techs,vintage)
                $(transfer_availTech(linksModelToCalc,years_a,transfer_techs,vintage)
                    and accounting_transferLinks(indicator,linksModelToCalc,years_a,transfer_techs,vintage,"useAnnuity") = 1
                    and years_a.val + accounting_transferLinks(indicator,linksModelToCalc,years_a,transfer_techs,vintage,"amorTime") > yearsSel.val
                    and years_a.val <= yearsSel.val ),
        transfer_linksBuild(linksModelToCalc,years_a,transfer_techs,vintage)
        * accounting_transferLinks(indicator,linksModelToCalc,years_a,transfer_techs,vintage,"perLinkBuild")
        * accounting_annuityFactor_transferLink(indicator,linksModelToCalc,years_a,transfer_techs,vintage) )

    + sum ((transfer_techs,vintage,link_types)
                $(transfer_availTech(linksModelToCalc,yearsSel,transfer_techs,vintage)
                    and accounting_transferPerLength(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"useAnnuity") = 0 ),
        transfer_linksBuild(linksModelToCalc,yearsSel,transfer_techs,vintage)
        * transfer_lengthParam(linksModelToCalc,link_types,"length")
        * accounting_transferPerLength(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perLengthBuild") )

    + sum ((years_a,transfer_techs,vintage,link_types)
                $(transfer_availTech(linksModelToCalc,years_a,transfer_techs,vintage)
                    and accounting_transferPerLength(indicator,linksModelToCalc,years_a,transfer_techs,vintage,link_types,"useAnnuity") = 1
                    and years_a.val + accounting_transferPerLength(indicator,linksModelToCalc,years_a,transfer_techs,vintage,link_types,"amorTime") > yearsSel.val
                    and years_a.val <= yearsSel.val ),
        transfer_linksBuild(linksModelToCalc,years_a,transfer_techs,vintage)
        * transfer_lengthParam(linksModelToCalc,link_types,"length")
        * accounting_transferPerLength(indicator,linksModelToCalc,years_a,transfer_techs,vintage,link_types,"perLengthBuild")
        * accounting_annuityFactor_transferPerLength(indicator,linksModelToCalc,years_a,transfer_techs,vintage,link_types) )

    + sum ((transfer_techs,vintage)
                $(transfer_decomTech(linksModelToCalc,yearsSel,transfer_techs,vintage)
                    and transfer_techParam(transfer_techs,vintage,'freeDecom')),
        transfer_linksDecom(linksModelToCalc,yearsSel,transfer_techs,vintage)
        * accounting_transferLinks(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,"perLinkDecom")

        + sum (link_types,
            transfer_linksDecom(linksModelToCalc,yearsSel,transfer_techs,vintage)
            * transfer_lengthParam(linksModelToCalc,link_types,"length")
            * accounting_transferPerLength(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perLengthDecom")
        ) )

    + sum ((transfer_techs,vintage)
                $(transfer_usedTech(linksModelToCalc,yearsSel,transfer_techs,vintage)),
        + transfer_linksTotal(linksModelToCalc,yearsSel,transfer_techs,vintage)
        * accounting_transferLinks(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,"perLinkTotal")

        + sum (link_types,
            + transfer_linksTotal(linksModelToCalc,yearsSel,transfer_techs,vintage)
            * transfer_lengthParam(linksModelToCalc,link_types,"length")
            * accounting_transferPerLength(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perLengthTotal"))

        + sum (timeModelSel,
            transfer_flowAlong(timeModelSel,linksModelToCalc,yearsSel,transfer_techs,vintage)
            * timeLength(timeModelSel)
            * ( accounting_transferLinks(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,"perFlow")
                + accounting_transferLinks(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,"perFlowAlong"))

            + transfer_flowAgainst(timeModelSel,linksModelToCalc,yearsSel,transfer_techs,vintage)
            * timeLength(timeModelSel)
            * ( accounting_transferLinks(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,"perFlow")
                + accounting_transferLinks(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,"perFlowAgainst")))
            / timefrac

        + sum ((timeModelSel, link_types),
            transfer_flowAlong(timeModelSel,linksModelToCalc,yearsSel,transfer_techs,vintage)
            * timeLength(timeModelSel)
            * transfer_lengthParam(linksModelToCalc,link_types,"length")
            * (accounting_transferPerLength(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perFlow")
                + accounting_transferPerLength(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perFlowAlong"))

            + transfer_flowAgainst(timeModelSel,linksModelToCalc,yearsSel,transfer_techs,vintage)
            * timeLength(timeModelSel)
            * transfer_lengthParam(linksModelToCalc,link_types,"length")
            * (accounting_transferPerLength(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perFlow")
                + accounting_transferPerLength(indicator,linksModelToCalc,yearsSel,transfer_techs,vintage,link_types,"perFlowAgainst")))
            / timefrac
        )
