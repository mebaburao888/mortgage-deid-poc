# Start the mortgage de-ID POC web interface
Write-Host "Starting API server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; uvicorn api:app --reload --port 8000"

Start-Sleep -Seconds 2

Write-Host "Starting UI dev server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\ui'; npm run dev"

Start-Sleep -Seconds 3
Write-Host "Opening browser..."
Start-Process "http://localhost:5173"
