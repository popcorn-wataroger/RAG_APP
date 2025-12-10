@echo off
cd /d c:\Users\User\Desktop\ragbot
echo ============================================================
echo RAGBOTサーバーを起動しています...
echo ============================================================
echo URL: http://localhost:8000
echo Swagger UI: http://localhost:8000/docs
echo.
echo 終了するには Ctrl+C を押してください
echo ============================================================
echo.

.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000

pause
