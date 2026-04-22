@echo off
cd /d "C:\Users\mikep\Claude LAE Market Services"
echo [%DATE% %TIME%] Sync von GitHub ... >> sync.log 2>&1
git pull origin main >> sync.log 2>&1
echo [%DATE% %TIME%] Fertig. >> sync.log 2>&1
