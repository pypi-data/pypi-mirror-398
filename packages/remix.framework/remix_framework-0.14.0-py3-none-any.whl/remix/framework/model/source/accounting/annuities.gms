* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

* Calculation of annuities
abort$(sum((indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage)
        $(accounting_converterUnits(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage,"useAnnuity") = 1
        and accounting_converterUnits(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage,"amorTime") < 1), 1) > 0 )
    "Accounting: Some converter technologies use annuities but have no amortization time"

parameter accounting_annuityFactor_converter(indicator,nodesModel,years,converter_techs,vintage);
accounting_annuityFactor_converter(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage)
    $accounting_converterUnits(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage,"useAnnuity")
    = 
    accounting_converterUnits(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage,"interest")
        * (1 + accounting_converterUnits(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage,"interest"))
        ** accounting_converterUnits(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage,"amorTime")
    / ((1 + accounting_converterUnits(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage,"interest"))
        ** accounting_converterUnits(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage,"amorTime") - 1);


abort$(sum((indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage)
        $(accounting_storageUnits(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage,"useAnnuity") = 1
        and accounting_storageUnits(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage,"amorTime") < 1), 1) > 0 )
    "Accounting: Some storage technologies use annuities but have no amortization time"

parameter accounting_annuityFactor_storage(indicator,nodesModel,years,storage_techs,vintage);
accounting_annuityFactor_storage(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage)
    $accounting_storageUnits(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage,"useAnnuity")
    = 
    accounting_storageUnits(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage,"interest")
        * (1 + accounting_storageUnits(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage,"interest"))
        ** accounting_storageUnits(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage,"amorTime")
    / ((1 + accounting_storageUnits(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage,"interest"))
        ** accounting_storageUnits(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage,"amorTime") - 1);


abort$(sum((indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage)
        $(accounting_transferLinks(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"useAnnuity") = 1
        and accounting_transferLinks(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"amorTime") < 1), 1) > 0 )
    "Accounting: Some transfer technologies use annuities but have no amortization time"

parameter accounting_annuityFactor_transferLink(indicator,linksModel,years,transfer_techs,vintage);
accounting_annuityFactor_transferLink(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage)
    $accounting_transferLinks(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"useAnnuity")
    = 
    accounting_transferLinks(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"interest")
        * (1 + accounting_transferLinks(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"interest"))
        ** accounting_transferLinks(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"amorTime")
    / ((1 + accounting_transferLinks(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"interest"))
        ** accounting_transferLinks(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,"amorTime") - 1);



abort$(sum((indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types)
        $(accounting_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"useAnnuity") = 1
        and accounting_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"amorTime") < 1), 1) > 0 )
    "Accounting: Some transfer-per-length technologies use annuities but have no amortization time"

parameter accounting_annuityFactor_transferPerLength(indicator,linksModel,years,transfer_techs,vintage,link_types);
accounting_annuityFactor_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types) = 1;
    
accounting_annuityFactor_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types)
    $accounting_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"useAnnuity")
    = 
    accounting_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"interest")
        * (1 + accounting_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"interest"))
        ** accounting_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"amorTime")
    / ((1 + accounting_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"interest"))
        ** accounting_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types,"amorTime") - 1);

$onVerbatim
$ifthene.roundcoefs %roundcoefs%=1
accounting_annuityFactor_converter(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage)
    = round(accounting_annuityFactor_converter(indicator,nodesModelToCalc,yearsToCalc,converter_techs,vintage), %roundcoefsdigits%);
accounting_annuityFactor_storage(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage)
    = round(accounting_annuityFactor_storage(indicator,nodesModelToCalc,yearsToCalc,storage_techs,vintage), %roundcoefsdigits%);
accounting_annuityFactor_transferLink(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage)
    = round(accounting_annuityFactor_transferLink(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage), %roundcoefsdigits%);
accounting_annuityFactor_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types)
    = round(accounting_annuityFactor_transferPerLength(indicator,linksModelToCalc,yearsToCalc,transfer_techs,vintage,link_types), %roundcoefsdigits%);
$endif.roundcoefs
$offVerbatim
