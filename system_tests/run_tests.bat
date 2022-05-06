@echo off
setlocal
REM Run this directory's tests using the IOC Testing Framework

call "%~dp0..\..\..\..\config_env.bat"

REM Command line arguments always passed to the test script
SET ARGS=--test_and_emulator %~dp0
call %PYTHON3% -u "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" %ARGS% %*
IF %ERRORLEVEL% NEQ 0 EXIT /b %ERRORLEVEL%
