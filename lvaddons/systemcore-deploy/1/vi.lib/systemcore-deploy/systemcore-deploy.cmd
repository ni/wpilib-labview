@echo off
rem Runs systemcore-deploy, a POSIX shell script, with Git for Windows' sh. The LabVIEW deploy tool
rem calls this through System Exec on Windows; arguments are passed through (systemcore-deploy --help).
setlocal
set "SCRIPT=%~dp0systemcore-deploy"
rem sh's dirname only understands forward slashes
set "SCRIPT=%SCRIPT:\=/%"

set "SH=%SYSTEMCORE_DEPLOY_SH%"
if defined SH if exist "%SH%" goto run
rem Git for Windows has git.exe in <Git>\cmd or <Git>\mingw64\bin, and sh.exe in <Git>\bin
for /f "delims=" %%G in ('where git.exe 2^>nul') do (
    if exist "%%~dpG..\bin\sh.exe" set "SH=%%~dpG..\bin\sh.exe" & goto run
    if exist "%%~dpG..\..\bin\sh.exe" set "SH=%%~dpG..\..\bin\sh.exe" & goto run
)
for /f "tokens=2,*" %%A in ('reg query "HKLM\SOFTWARE\GitForWindows" /v InstallPath 2^>nul ^| find "InstallPath"') do set "GITDIR=%%B"
if defined GITDIR if exist "%GITDIR%\bin\sh.exe" set "SH=%GITDIR%\bin\sh.exe" & goto run
if exist "%ProgramFiles%\Git\bin\sh.exe" set "SH=%ProgramFiles%\Git\bin\sh.exe" & goto run

echo systemcore-deploy: error: Git for Windows isn't installed (https://git-scm.com/download/win)
echo SYSTEMCORE-TOOL: RESULT ERROR NO_GIT
exit /b 1

:run
"%SH%" "%SCRIPT%" %*
exit /b %ERRORLEVEL%
