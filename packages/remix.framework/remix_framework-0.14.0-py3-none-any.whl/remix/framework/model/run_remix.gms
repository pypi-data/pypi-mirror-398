* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

* ==== REMix version number ====
$setglobal remixversion 0.14.0

* ==== global settings ====
$if not set sourcedir           $setglobal sourcedir                 %gams.workdir%%system.dirsep%source
$if not set datadir             $setglobal datadir                   %gams.workdir%
$if not set scendir             $setglobal scendir                   .
$if not set instancedir         $setglobal instancedir               %gams.scrdir%
$onVerbatim
$if not set buildmodel          $setglobal buildmodel                1
$if not set solvemodel          $setglobal solvemodel                1
$if not set metadata            $setglobal metadata                  1
$ife %buildmodel%=0             $setglobal metadata                  0
$offVerbatim

$if not dexist "%datadir%/%scendir%" $abort "Error: Data directory %datadir%/%scendir% not found!"

* ==== write metadata and inherit dataset ====
$include "%sourcedir%/metadata.gms"
$include "%sourcedir%/data_inheritance.gms"

* ==== run remix ====
$onVerbatim
$iftheni.test_inputdata %test%==inputdata
$offVerbatim
$log "Testing input data, model will not be solved"
$include "%sourcedir%/methods/test_inputdata.gms"
$onVerbatim
$else.test_inputdata
$offVerbatim
$include "%sourcedir%/remix.gms"
$onVerbatim
$endif.test_inputdata
$offVerbatim
