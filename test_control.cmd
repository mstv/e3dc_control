set CTRL=python -u control\main.py
set ELOG=%TEMP%\test_control.err
%CTRL% --info --num-loops=1 2> %ELOG%
%CTRL% -in1 2>> %ELOG%
%CTRL% --verbose --info --num-loops=1 2>> %ELOG%
%CTRL% -vin1 2>> %ELOG%
%CTRL% --dry-run --num-loops=2 --wait=.2 2>> %ELOG%
%CTRL% -dn2 -w.2 2>> %ELOG%
%CTRL% --tag=EMS_REQ_POWER_PV 2>> %ELOG%
%CTRL% -tEMS_REQ_POWER_PV 2>> %ELOG%
%CTRL% --wb=5:0 2>> %ELOG%
%CTRL% --wb=5:0:ext 2>> %ELOG%
%CTRL% --wb=5:0:0 2>> %ELOG%

type %ELOG%

%CTRL% -w3 2>> %ELOG%
