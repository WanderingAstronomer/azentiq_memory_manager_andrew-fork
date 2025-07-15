@echo off
echo ===================================================================
echo IoT Agent Demo Setup and Execution
echo ===================================================================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3.11 or higher is required but not found.
    echo Please install Python from https://www.python.org/downloads/
    exit /b 1
)

REM Check if Python version is at least 3.11
for /f "tokens=2" %%I in ('python --version 2^>^&1') do (
    for /f "tokens=1,2,3 delims=." %%A in ("%%I") do (
        if %%A LSS 3 (
            echo ERROR: Python version 3.11 or higher is required.
            echo Current version: %%A.%%B.%%C
            exit /b 1
        ) else (
            if %%A EQU 3 (
                if %%B LSS 11 (
                    echo ERROR: Python version 3.11 or higher is required.
                    echo Current version: %%A.%%B.%%C
                    exit /b 1
                )
            )
        )
    )
)

REM Check if Docker is running
docker ps > nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Docker does not appear to be running.
    echo Redis is required for this demo. Make sure Docker Desktop is running.
    echo.
    set /p continue="Do you want to continue anyway? (y/n): "
    if /i not "%continue%" == "y" exit /b 1
    echo.
) else (
    echo Docker is running. Checking for Redis container...
    
    REM Check if Redis container is running
    docker ps | findstr "redis" > nul
    if %errorlevel% neq 0 (
        echo Redis container not found. Attempting to start one...
        docker run --name redis-memory-store -p 6379:6379 -d redis
        if %errorlevel% neq 0 (
            echo Failed to start Redis container. Please start it manually:
            echo docker run --name redis-memory-store -p 6379:6379 -d redis
        ) else (
            echo Redis container started successfully.
        )
    ) else (
        echo Redis container is already running.
    )
)

echo.
echo ===================================================================
echo Setting up virtual environment
echo ===================================================================

REM Navigate to the project root directory (up two levels from the script location)
cd /d "%~dp0..\.."
set PROJECT_ROOT=%cd%

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Add the project root to PYTHONPATH instead of installing in development mode
echo Setting up Python path for Azentiq Memory Manager...
set PYTHONPATH=%PROJECT_ROOT%
echo Project root added to PYTHONPATH: %PROJECT_ROOT%

REM Navigate to the IoT agent directory
cd samples\langchain_iot_agent

REM Install requirements
echo Installing required packages...
pip install -r requirements.txt

REM Set OpenAI API key if not already set
if not defined OPENAI_API_KEY (
    echo.
    echo ===================================================================
    echo OpenAI API Key Setup
    echo ===================================================================
    echo.
    echo OPENAI_API_KEY environment variable is not set.
    echo You will be prompted for your API key when running the demo.
    echo.
    echo To avoid this prompt in the future, you can set it permanently:
    echo - For PowerShell: $env:OPENAI_API_KEY="your_api_key"
    echo - For Command Prompt: set OPENAI_API_KEY=your_api_key
    echo.
)

REM Check if Redis Commander is wanted
echo.
echo ===================================================================
echo Optional: Redis Commander (Web UI for Redis)
echo ===================================================================
set /p install_commander="Do you want to set up Redis Commander for visualizing memory? (y/n): "
if /i "%install_commander%" == "y" (
    echo Setting up Redis Commander...
    docker ps | findstr "redis-commander" > nul
    if %errorlevel% neq 0 (
        docker run --name redis-commander -d --restart always ^
        -p 8081:8081 ^
        -e REDIS_HOSTS=local:redis-memory-store:6379 ^
        --network=host ^
        rediscommander/redis-commander
        
        if %errorlevel% neq 0 (
            echo Failed to start Redis Commander. You can start it manually with:
            echo docker run --name redis-commander -d --restart always ^
            echo -p 8081:8081 -e REDIS_HOSTS=local:redis-memory-store:6379 --network=host rediscommander/redis-commander
        ) else (
            echo Redis Commander started successfully.
            echo Access the web UI at: http://localhost:8081
        )
    ) else (
        echo Redis Commander is already running.
        echo Access the web UI at: http://localhost:8081
    )
)

echo.
echo ===================================================================
echo Running IoT Agent Demo
echo ===================================================================
echo.
echo Demo will start now. You can:
echo - Watch telemetry processing and anomaly detection
echo - Ask natural language questions about device history
echo - Press Ctrl+C to exit the demo
echo.
echo If Redis Commander is running, you can view memory contents at:
echo http://localhost:8081
echo.
pause
python demo.py

REM Keep the window open after demo completes or errors
pause
