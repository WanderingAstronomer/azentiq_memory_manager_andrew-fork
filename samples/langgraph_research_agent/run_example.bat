@echo off
echo Azentiq Memory Manager - LangGraph Research Agent Example
echo =======================================================

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    goto :EOF
)

REM Set up virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install required packages
echo Installing required packages...
cd ..\..\ 
pip install . langchain langgraph langchain_openai redis
cd samples\langgraph_research_agent

REM Check for Redis
echo Checking Redis connection...
python -c "import redis; redis.Redis(host='localhost', port=6379).ping()" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Trying alternate Redis port 8081...
    python -c "import redis; redis.Redis(host='localhost', port=8081).ping()" >nul 2>nul
)
if %ERRORLEVEL% neq 0 (
    echo WARNING: Redis server not running or not accessible on localhost:6379.
    echo Please make sure Redis is running before continuing.
    pause
)

REM Check for OpenAI API Key
if "%OPENAI_API_KEY%"=="" (
    echo OpenAI API Key not set in environment.
    set /p OPENAI_API_KEY="Enter your OpenAI API Key: "
)

REM Set Redis URL to use port 8081
set REDIS_URL=redis://localhost:8081/0

REM Run the example
echo Running LangGraph Research Agent Example...
python example.py

REM Deactivate the virtual environment
deactivate

echo.
echo Example finished.
pause
