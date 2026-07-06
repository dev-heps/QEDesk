@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_DIR=%%~fI"
set "SERVICE=qedesk"
set "PDF_BUILD_DIR=build"
set "COMMAND=%~1"

if "%COMMAND%"=="" set "COMMAND=help"

if "%COMMAND%"=="shell" call :require_running || exit /b 1
if "%COMMAND%"=="lean" call :require_running || exit /b 1
if "%COMMAND%"=="build-lean" call :require_running || exit /b 1
if "%COMMAND%"=="pdf" call :require_running || exit /b 1
if "%COMMAND%"=="agent" call :require_running || exit /b 1

if "%COMMAND%"=="start" (
  docker compose --project-directory "%PROJECT_DIR%" up -d
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="stop" (
  docker compose --project-directory "%PROJECT_DIR%" down
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="restart" (
  docker compose --project-directory "%PROJECT_DIR%" down
  docker compose --project-directory "%PROJECT_DIR%" up -d
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="status" (
  docker compose --project-directory "%PROJECT_DIR%" ps
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="shell" (
  docker compose --project-directory "%PROJECT_DIR%" exec "%SERVICE%" bash
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="files" (
  echo Edit these files in your editor:
  echo.
  echo   Lean source:   %PROJECT_DIR%\src\Proof.lean
  echo   LaTeX notes:   %PROJECT_DIR%\src\main.tex
  echo   PDF output:    %PROJECT_DIR%\%PDF_BUILD_DIR%\main.pdf
  echo.
  echo Do not run src\Proof.lean or src\main.tex as shell commands.
  echo Use:
  echo.
  echo   bin\qedesk.bat lean
  echo   bin\qedesk.bat pdf
  exit /b 0
)
if "%COMMAND%"=="lean" (
  docker compose --project-directory "%PROJECT_DIR%" exec "%SERVICE%" lake build Proof
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="build-lean" (
  docker compose --project-directory "%PROJECT_DIR%" exec "%SERVICE%" lake build Proof
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="pdf" (
  if not exist "%PROJECT_DIR%\%PDF_BUILD_DIR%" mkdir "%PROJECT_DIR%\%PDF_BUILD_DIR%"
  docker compose --project-directory "%PROJECT_DIR%" exec "%SERVICE%" latexmk -pdf -g -shell-escape -interaction=nonstopmode -halt-on-error -output-directory=%PDF_BUILD_DIR% src/main.tex
  if errorlevel 1 (
    echo.
    echo Could not write build\main.pdf. If it is open in a PDF viewer, close it and retry.
    echo Trying build\main-preview.pdf instead...
    docker compose --project-directory "%PROJECT_DIR%" exec "%SERVICE%" latexmk -pdf -g -jobname=main-preview -shell-escape -interaction=nonstopmode -halt-on-error -output-directory=%PDF_BUILD_DIR% src/main.tex
  )
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="agent" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" uvx lean-lsp-mcp
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="clean" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" rm -rf .lake lake-manifest.json %PDF_BUILD_DIR% _minted-* *.aux *.fdb_latexmk *.fls *.log *.out *.pdf 2>nul
  if errorlevel 1 powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%PROJECT_DIR%'; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .lake, lake-manifest.json, %PDF_BUILD_DIR%, _minted-*, *.aux, *.fdb_latexmk, *.fls, *.log, *.out, *.pdf"
  exit /b 0
)
if "%COMMAND%"=="docker-clean" (
  docker compose --project-directory "%PROJECT_DIR%" down --remove-orphans
  docker image rm -f qedesk
  exit /b 0
)
if "%COMMAND%"=="help" goto :help
if "%COMMAND%"=="-h" goto :help
if "%COMMAND%"=="--help" goto :help

echo Unknown command: %COMMAND% 1>&2
echo. 1>&2
goto :help_error

:help
echo QEDesk command line
echo.
echo Usage:
echo   qedesk ^<command^>
echo.
echo Commands:
echo   start         Build and start the QEDesk container
echo   stop          Stop and remove the container
echo   restart       Restart the container
echo   status        Show container status
echo   shell         Open a shell inside the container
echo   files         Show the main files to edit
echo   lean          Build the Lean library
echo   build-lean    Alias for lean
echo   pdf           Build build/main.pdf from src/main.tex
echo   agent         Run lean-lsp-mcp inside the container
echo   clean         Remove local build artifacts
echo   docker-clean  Remove the local QEDesk container and image
exit /b 0

:help_error
call :help
exit /b 2

:require_running
for /f %%S in ('docker compose --project-directory "%PROJECT_DIR%" ps --status running --services 2^>nul') do (
  if "%%S"=="%SERVICE%" exit /b 0
)
echo QEDesk is not running. Start it first: 1>&2
echo. 1>&2
echo   bin\qedesk.bat start 1>&2
exit /b 1
