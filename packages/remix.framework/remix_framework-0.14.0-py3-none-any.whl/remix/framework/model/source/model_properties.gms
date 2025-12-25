* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

* ==== Overview of model dimensions ====
parameters  acts(converter_techs) "active technologies"
            asts(storage_techs) "active storage technologies"
            atts(transfer_techs) "active transfer technologies"

scalars nd "number of dispatch time steps per year"
        nn "number of network nodes"
        nl "number of network links"
        nt "number of converter, storage and transfer technologies"
        nc "number of commodities"
        ny "number of years of the capacity planning horizon";

option acts < converter_availTech;
option asts < storage_availTech;
option atts < transfer_availTech;

nd = sum (timeModel $timeModelToCalc(timeModel), 1);
nn = sum (nodesModel $nodesModelToCalc(nodesModel), 1);
nl = sum (linksModel $linksModelToCalc(linksModel), 1);
nt = sum (storage_techs $asts(storage_techs), 1)
    + sum (converter_techs $acts(converter_techs), 1)
    + sum (transfer_techs $atts(transfer_techs), 1);
nc = card(commodity);
ny = sum (years $yearsToCalc(years), 1);

file props / '' /;
put props;
put "### Model properties  ###" /;
put "Number of active dispatch time steps per year: " nd:0:0  /;
put "Number of active network nodes: " nn:0:0  /;
put "Number of active network links: " nl:0:0  /;
put "Number of active converter, storage and transfer technologies: " nt:0:0  /;
put "Number of commodities: " nc:0:0  /;
put "Number of years considered for capacity expansion: " ny:0:0  /;
putclose;
