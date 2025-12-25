* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

$setargs paramName paramIdxPre accType paramIdxPost checkAnnuity

$if "%checkAnnuity%"=="" $setlocal checkAnnuity 0

set %paramName%Nonzero(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%);
%paramName%Nonzero(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%)
    $sum(pc_%paramName%$%paramName%In(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%,pc_%paramName%), 1)
    = yes;

$ifthen.checkAnnuity "%checkAnnuity%"=="1"
set %paramName%Chk(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%);
%paramName%Chk(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,"useAnnuity")
    $sum((%accType%Data,acc%accType%Data)
            $(aggregate%accType%Model(%accType%Data,%accType%Model) and sameas(%accType%Data,acc%accType%Data)
                and %paramName%Nonzero(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%)), 1)
    = smax((%accType%Data,acc%accType%Data)
            $(aggregate%accType%Model(%accType%Data,%accType%Model) and sameas(%accType%Data,acc%accType%Data)
                and %paramName%Nonzero(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%)),
        %paramName%In(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%,"useAnnuity"))
    - smin((%accType%Data,acc%accType%Data)
            $(aggregate%accType%Model(%accType%Data,%accType%Model) and sameas(%accType%Data,acc%accType%Data)
                and %paramName%Nonzero(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%)),
        %paramName%In(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%,"useAnnuity"));

abort$sum(%paramName%Chk(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%), 1) "Cannot aggregate technologies with different useAnnuity values."
$endif.checkAnnuity

parameter %paramName%Agg(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%);
%paramName%Agg(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%)
    $sum((%accType%Data,acc%accType%Data)
            $(aggregate%accType%Model(%accType%Data,%accType%Model) and sameas(%accType%Data,acc%accType%Data)
                and %paramName%Nonzero(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%)), 1)
    = sum((%accType%Data,acc%accType%Data)
            $(aggregate%accType%Model(%accType%Data,%accType%Model) and sameas(%accType%Data,acc%accType%Data)
                and %paramName%Nonzero(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%)),
        %paramName%In(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%,pc_%paramName%))
    / sum((%accType%Data,acc%accType%Data)
            $(aggregate%accType%Model(%accType%Data,%accType%Model) and sameas(%accType%Data,acc%accType%Data)
                and %paramName%Nonzero(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%)),
        1);

parameter %paramName%In2(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%);
loop(acc%accType%,
%paramName%In2(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%)
    $sum(acc%accType%Data$(map_acc%accType%ToCalc(acc%accType%,%accType%Model) and sameas(acc%accType%,acc%accType%Data)
                            and %paramName%In(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%,pc_%paramName%)), 1)
    = sum(acc%accType%Data$(map_acc%accType%ToCalc(acc%accType%,%accType%Model) and sameas(acc%accType%,acc%accType%Data)),
            %paramName%In(%paramIdxPre%,acc%accType%Data,accYears,%paramIdxPost%,pc_%paramName%));
);

%paramName%In2(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%)
    $%paramName%Agg(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%)
    = %paramName%Agg(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%);

parameter %paramName%(%paramIdxPre%,%accType%Model,years,%paramIdxPost%,pc_%paramName%);
loop(accYears,
%paramName%(%paramIdxPre%,%accType%Model,years,%paramIdxPost%,pc_%paramName%)
    $sum(accYears_a$(map_accYearsToCalc(accYears,years) and sameas(accYears_a, years)
            and %paramName%In2(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%)), 1)
    = sum(accYears_a$(map_accYearsToCalc(accYears,years) and sameas(accYears_a, years)),
            %paramName%In2(%paramIdxPre%,%accType%Model,accYears,%paramIdxPost%,pc_%paramName%))
);

* option kill %paramName%Nonzero %paramName%Chk %paramName%Agg