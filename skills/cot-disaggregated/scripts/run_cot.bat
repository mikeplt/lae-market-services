@echo off
cd /d "C:\Users\mikep\Claude LAE Market Services"
echo [%DATE% %TIME%] COT Disaggregated wird generiert ...
python skills\cot-disaggregated\scripts\generate.py
pause
