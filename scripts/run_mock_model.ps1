Set-Location "$PSScriptRoot\..\services\mock-model"
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
