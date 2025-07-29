@echo off
echo ===================================================
echo Azentiq Memory Manager API Service Runner
echo ===================================================
echo.

REM Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found. Please ensure Python is installed and in your PATH.
    exit /b 1
)

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Check for command line arguments
if "%1"=="test" goto run_tests
if "%1"=="install" goto install_deps

:run_service
echo Starting Memory Manager API service...
echo.
echo API will be available at http://localhost:8000
echo Swagger UI docs will be available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the service
echo.
python -m services.run_api --reload
goto end

:run_tests
echo Running API tests...
echo.
echo Note: Make sure the API service is running in another terminal
echo before running tests.
echo.
set /p answer=Is the API service running? (Y/N): 
if /i "%answer%"=="Y" (
    python -m services.test_api
) else (
    echo Please start the API service first using:
    echo run_api_service.bat
)
goto end

:install_deps
echo Installing required dependencies...
pip install -r requirements.txt
echo.
echo Dependencies installed.
echo.
echo To start the API service, run:
echo run_api_service.bat
echo.
echo To run API tests, run:
echo run_api_service.bat test
goto end

:help
echo Usage:
echo run_api_service.bat         - Start the API service
echo run_api_service.bat test    - Run API tests
echo run_api_service.bat install - Install required dependencies
goto end

:end
