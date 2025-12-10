@echo off
REM test_ask.bat - ASKエンドポイントをテスト
echo ASK エンドポイントをテストします...
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"query\":\"GPTとGeminiの違いは何ですか？\"}"
echo.
echo テスト完了
pause
