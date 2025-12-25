* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

* // # accounting_equations

* ==== declaration of variables ====

variables
accounting_indicator(accNodesModel,accYears,indicator)
accounting_indicator_links(linksModel,years,indicator)
accounting_objective
;


* ==== definition of variables ====

accounting_indicator.lo(accNodesModel,accYears,indicator)
    $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"useLower")
        and accounting_indicatorBounds(accNodesModel,accYears,indicator,"isVariable"))
    = accounting_indicatorBounds(accNodesModel,accYears,indicator,"lowerValue");

accounting_indicator.up(accNodesModel,accYears,indicator)
    $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"useUpper")
        and accounting_indicatorBounds(accNodesModel,accYears,indicator,"isVariable"))
    = accounting_indicatorBounds(accNodesModel,accYears,indicator,"upperValue");

accounting_indicator.fx(accNodesModel,accYears,indicator)
    $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"useFixed")
        and accounting_indicatorBounds(accNodesModel,accYears,indicator,"isVariable"))
    = accounting_indicatorBounds(accNodesModel,accYears,indicator,"fixedValue");


* set the variable levels to be fixed for years before the optimization years
accounting_indicator.l(accNodesModel,accYears,indicator)
    $activeIndicators(accNodesModel,accYears,indicator)
    = 0;


* ==== declaration of equations ====

equations
Eq_accounting_indicatorCalc_fixed(accNodesModel,accYears,indicator
    ) "Ensures the fixed value of an indicator per accounting region"
Eq_accounting_indicatorCalc_upper(accNodesModel,accYears,indicator
    ) "Ensures the upper limit of an indicator per accounting region"
Eq_accounting_indicatorCalc_lower(accNodesModel,accYears,indicator
    ) "Ensures the lower limit of an indicator per accounting region"
Eq_accounting_indicatorCalc_links_fixed(linksModel,years,indicator
    ) "Ensures the fixed value of an indicator per model link"
Eq_accounting_indicatorCalc_links_upper(linksModel,years,indicator
    ) "Ensures the upper limit of an indicator per model link"
Eq_accounting_indicatorCalc_links_lower(linksModel,years,indicator
    ) "Ensures the lower limit of an indicator per model link"
Eq_accounting_objective "Calculates the objective value based on the specified indicator"
  ;


* ==== equations definition ====
* // ## Equations
* // ### Accounting Indicator Calculation
* // Calculates the fixed limit for accounting indicators.
* // {Eq_accounting_indicatorCalc_fixed}
Eq_accounting_indicatorCalc_fixed(accNodesModel,accYearsSel(accYears),indicator)
    $(activeIndicators(accNodesModel,accYears,indicator)
        and accounting_indicatorBounds(accNodesModel,accYears,indicator,"useFixed"))
    ..
$include "%sourcedir%/accounting/inc_accnodes.gms"
    =e=
    accounting_indicatorBounds(accNodesModel,accYears,indicator,"fixedValue");

* // ### Accounting Indicator Calculation
* // Calculates the indicators for each model node for converters, sources and sinks, transfer, storage and variable indicators.
* // {Eq_accounting_indicatorCalc_upper}
Eq_accounting_indicatorCalc_upper(accNodesModel,accYearsSel(accYears),indicator)
    $(activeIndicators(accNodesModel,accYears,indicator)
        and accounting_indicatorBounds(accNodesModel,accYears,indicator,"useUpper")
        and not accounting_indicatorBounds(accNodesModel,accYears,indicator,"useFixed"))
    ..
$include "%sourcedir%/accounting/inc_accnodes.gms"
    =l=
    accounting_indicatorBounds(accNodesModel,accYears,indicator,"upperValue");

* // ### Accounting Indicator Calculation
* // Calculates the indicators for each model node for converters, sources and sinks, transfer, storage and variable indicators.
* // {Eq_accounting_indicatorCalc_lower}
Eq_accounting_indicatorCalc_lower(accNodesModel,accYearsSel(accYears),indicator)
    $(activeIndicators(accNodesModel,accYears,indicator)
        and accounting_indicatorBounds(accNodesModel,accYears,indicator,"useLower")
        and not accounting_indicatorBounds(accNodesModel,accYears,indicator,"useFixed"))
    ..
$include "%sourcedir%/accounting/inc_accnodes.gms"
    =g=
    accounting_indicatorBounds(accNodesModel,accYears,indicator,"lowerValue");


* // ### Accounting Indicator Calculation Links
* // Calculates the indicators for each transfer for converters, sources and sinks, transfer, storage and variable indicators.
* // {Eq_accounting_indicatorCalc_links_fixed}
Eq_accounting_indicatorCalc_links_fixed(linksModelToCalc,yearsSel,indicator)
    $(activeIndicators_links(linksModelToCalc,yearsSel,indicator)
        and accounting_indicatorBounds_links(linksModelToCalc,yearsSel,indicator,"useFixed"))
    ..
$include "%sourcedir%/accounting/inc_acclinks.gms"
    =e=
accounting_indicatorBounds_links(linksModelToCalc,yearsSel,indicator,"fixedValue");

* // ### Accounting Indicator Calculation Links
* // Calculates the indicators for each transfer for converters, sources and sinks, transfer, storage and variable indicators.
* // {Eq_accounting_indicatorCalc_links_upper}
Eq_accounting_indicatorCalc_links_upper(linksModelToCalc,yearsSel,indicator)
    $(activeIndicators_links(linksModelToCalc,yearsSel,indicator)
        and accounting_indicatorBounds_links(linksModelToCalc,yearsSel,indicator,"useUpper")
        and not accounting_indicatorBounds_links(linksModelToCalc,yearsSel,indicator,"useFixed"))
    ..
$include "%sourcedir%/accounting/inc_acclinks.gms"
    =l=
accounting_indicatorBounds_links(linksModelToCalc,yearsSel,indicator,"upperValue");

* // ### Accounting Indicator Calculation Links
* // Calculates the indicators for each transfer for converters, sources and sinks, transfer, storage and variable indicators.
* // {Eq_accounting_indicatorCalc_links_lower}
Eq_accounting_indicatorCalc_links_lower(linksModelToCalc,yearsSel,indicator)
    $(activeIndicators_links(linksModelToCalc,yearsSel,indicator)
        and accounting_indicatorBounds_links(linksModelToCalc,yearsSel,indicator,"useLower")
        and not accounting_indicatorBounds_links(linksModelToCalc,yearsSel,indicator,"useFixed"))
    ..
$include "%sourcedir%/accounting/inc_acclinks.gms"
    =g=
accounting_indicatorBounds_links(linksModelToCalc,yearsSel,indicator,"lowerValue");


* // ### Accounting Objective
* // Calculates the indicators for the objective.
* // {Eq_accounting_objective}
Eq_accounting_objective
    ..
    accounting_objective
    =e=
    sum ((accNodesModel,accYears,indicator)
            $(accounting_indicatorBounds(accNodesModel,accYears,indicator,"obj") <> 0 ),
        (-1 * accounting_indicatorBounds(accNodesModel,accYears,indicator,"obj"))
        *
$include "%sourcedir%/accounting/inc_accnodes.gms"
    )


* ==== model definition ====

Model M_accounting
/
Eq_accounting_indicatorCalc_fixed
Eq_accounting_indicatorCalc_upper
Eq_accounting_indicatorCalc_lower
Eq_accounting_indicatorCalc_links_fixed
Eq_accounting_indicatorCalc_links_upper
Eq_accounting_indicatorCalc_links_lower
Eq_accounting_objective
/;
