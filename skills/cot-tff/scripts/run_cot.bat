@echo off
cd /d "C:\Users\mikep\Claude LAE Market Services"
echo [%DATE% %TIME%] COT Report wird generiert ... >> outputs\cot-report\run.log
python skills\cot-report\scripts\generate.py >> outputs\cot-report\run.log 2>&1
echo [%DATE% %TIME%] Fertig. >> outputs\cot-report\run.log
