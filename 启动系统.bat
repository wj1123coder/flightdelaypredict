@echo off
echo 启动智能航班延误预测系统（简化版）
echo.

cd /d %~dp0

REM 激活虚拟环境
call venv\Scripts\activate

echo 1. 启动Flask服务器...
start cmd /k "cd backend && python app.py"

echo 等待服务器启动...
timeout /t 5 /nobreak >nul

echo 2. 打开浏览器...
start http://localhost:5000

echo.
echo ✅ 系统已启动！
echo 🌐 请访问: http://localhost:5000
echo.
pause