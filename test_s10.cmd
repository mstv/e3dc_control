set S10=python -u control\s10.py
set LOG=%TEMP%\test_s10.err
%S10% --info --num-loops=1 2> %LOG%
%S10% -in1 2>> %LOG%
%S10% --verbose --info --num-loops=1 2>> %LOG%
%S10% -vin1 2>> %LOG%
%S10% --dry-run --num-loops=2 --wait=.2 2>> %LOG%
%S10% -dn2 -w.2 2>> %LOG%
%S10% --tag=EMS_REQ_POWER_PV 2>> %LOG%
%S10% -tEMS_REQ_POWER_PV 2>> %LOG%
%S10% --wb=5:0 2>> %LOG%
%S10% --wb=5:0:ext 2>> %LOG%
%S10% --wb=5:0:0 2>> %LOG%

type %LOG%

%S10% -w3 2>> %LOG%
