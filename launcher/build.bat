@echo off
rem Builds the launcher with MSVC: launcher\build.bat OUT.exe
rem The workflow runs it on every build. Releases ship the signed copy
rem committed beside it as v-on-patcher.exe, once there is one.
setlocal
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
for /f "usebackq delims=" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -find VC\Auxiliary\Build\vcvars64.bat`) do set "VCVARS=%%i"
if not defined VCVARS (echo MSVC not found & exit /b 1)
call "%VCVARS%" >nul || exit /b 1
cd /d "%~dp0"
rc /nologo /fo "%TEMP%\launcher.res" launcher.rc || exit /b 1
cl /nologo /O1 /MT /W4 /WX /DUNICODE /D_UNICODE launcher.c "%TEMP%\launcher.res" /Fe"%~1" /Fo"%TEMP%\launcher.obj" /link /SUBSYSTEM:WINDOWS /MANIFEST:EMBED user32.lib || exit /b 1
