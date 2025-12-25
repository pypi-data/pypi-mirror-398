* SPDX-FileCopyrightText: Copyright (c) 2023-2024 German Aerospace Center (DLR)
* SPDX-License-Identifier: BSD-3-Clause

* Include metadata in logfile
$ifthene.shortmetadata %metadata%=0
$log ### Short metadata ###
$log Using REMix version %remixversion%
$log Using GAMS version %system.GamsReleaseMaint%
$log Using data directory %datadir% 
$log Using scenario directory %scendir%
$log Using framework path %sourcedir%
$log Using project path %datadir%%scendir%
$log Using instance directory %instancedir%

$else.shortmetadata

* Set OS specific options
$iftheni.os %system.FileSys%==msnt
$setglobal devnull ">nul 2>&1"
$setglobal pwd "cd|"
$else.os
$setglobal devnull "> /dev/null 2>&1"
$setglobal pwd "pwd|"
$endif.os

* Get general REMix information
$call 'printf "remix_version \"%remixversion%\"\n" > %gams.scrdir%%system.dirsep%metadata';
$call 'printf "gams_version \"%system.GamsReleaseMaint%\"\n" >> %gams.scrdir%%system.dirsep%metadata';
$call 'printf "timestamp \"%system.DATE% %system.TIME%\"\n" >> %gams.scrdir%%system.dirsep%metadata';

* Path to framework
$call 'printf "framework_path " >> %gams.scrdir%%system.dirsep%metadata';
$call 'cd %sourcedir% && %pwd% sed "s/^/\"/;s/$/\"/" >> %gams.scrdir%%system.dirsep%metadata';
$call 'printf "\n" >> %gams.scrdir%%system.dirsep%metadata';

* Hash of framework commit
$call 'printf "framework_hash " >> %gams.scrdir%%system.dirsep%metadata';
$call 'cd %sourcedir% && git rev-parse HEAD %devnull% && git rev-parse HEAD >> %gams.scrdir%%system.dirsep%metadata';
$call 'printf "\n" >> %gams.scrdir%%system.dirsep%metadata';

* Branch of framework
$call 'printf "framework_branch " >> %gams.scrdir%%system.dirsep%metadata';
$call 'cd %sourcedir% && git rev-parse --abbrev-ref HEAD %devnull% && git rev-parse --abbrev-ref HEAD | sed "s/^/\"/;s/$/\"/" >> %gams.scrdir%%system.dirsep%metadata';
$call 'printf "\n" >> %gams.scrdir%%system.dirsep%metadata';

* Path to project
$call 'printf "project_path " >> %gams.scrdir%%system.dirsep%metadata';
$call 'cd %datadir%%system.dirsep%%scendir% && %pwd% sed "s/^/\"/;s/$/\"/" >> %gams.scrdir%%system.dirsep%metadata';
$call 'printf "\n" >> %gams.scrdir%%system.dirsep%metadata';

* Hash of project commit
$call 'printf "project_hash " >> %gams.scrdir%%system.dirsep%metadata';
$call 'cd %datadir%%system.dirsep%%scendir% && git rev-parse HEAD %devnull% && git rev-parse HEAD | sed "s/^/\"/;s/$/\"/" >> %gams.scrdir%%system.dirsep%metadata';
$call 'printf "\n" >> %gams.scrdir%%system.dirsep%metadata';

* Branch of project
$call 'printf "project_branch " >> %gams.scrdir%%system.dirsep%metadata';
$call 'cd %datadir%%system.dirsep%%scendir% && git rev-parse --abbrev-ref HEAD %devnull% && git rev-parse --abbrev-ref HEAD | sed "s/^/\"/;s/$/\"/" >> %gams.scrdir%%system.dirsep%metadata';
$call 'printf "\n" >> %gams.scrdir%%system.dirsep%metadata';

* Include metadata in gdx file
set metadata(*) /
$include "%gams.scrdir%%system.dirsep%metadata"
/;

$log ### Full metadata ###
$call 'cat %gams.scrdir%%system.dirsep%metadata | grep -v "^$"';

$endif.shortmetadata



