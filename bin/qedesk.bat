@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_DIR=%%~fI"
set "SERVICE=qedesk"
set "PDF_BUILD_DIR=build"
set "COMMAND=%~1"

if "%COMMAND%"=="" set "COMMAND=help"

set "REQUIRE_RUNNING="
if "%COMMAND%"=="shell" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="sync" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="blueprint" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="serve" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="prepare" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="cache" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="lean" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="build-lean" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="pdf" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="agent" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="audit" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="formalize" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="repair" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="route" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="cost" set "REQUIRE_RUNNING=1"
if "%COMMAND%"=="init-ledger" set "REQUIRE_RUNNING=1"

if defined REQUIRE_RUNNING (
  set "QEDESK_RUNNING="
  for /f %%S in ('docker compose --project-directory "%PROJECT_DIR%" ps --status running --services 2^>nul') do (
    if "%%S"=="%SERVICE%" set "QEDESK_RUNNING=1"
  )
  if not defined QEDESK_RUNNING (
    echo QEDesk is not running. Start it first: 1>&2
    echo. 1>&2
    echo   bin\qedesk.bat start 1>&2
    exit /b 1
  )
)

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
  echo   Architecture:  %PROJECT_DIR%\docs\ARCHITECTURE.md
  echo   Data contract: %PROJECT_DIR%\docs\DATA_CONTRACTS.md
  echo   PDF output:    %PROJECT_DIR%\%PDF_BUILD_DIR%\main.pdf
  echo.
  echo Do not run src\Proof.lean or src\main.tex as shell commands.
  echo Use:
  echo.
  echo   bin\qedesk.bat lean
  echo   bin\qedesk.bat pdf
  exit /b 0
)
if "%COMMAND%"=="contracts" (
  echo QEDesk v0.2 data contracts:
  echo.
  echo   Architecture:       %PROJECT_DIR%\docs\ARCHITECTURE.md
  echo   Data contracts:     %PROJECT_DIR%\docs\DATA_CONTRACTS.md
  echo   Integrations:       %PROJECT_DIR%\docs\INTEGRATIONS.md
  echo   Agent rules:        %PROJECT_DIR%\AGENTS.md
  echo   OpenCode config:    %PROJECT_DIR%\opencode.json
  echo   Router config:      %PROJECT_DIR%\qedesk-router.json
  echo   DAG schema:         %PROJECT_DIR%\schemas\qedesk-dag.schema.json
  echo   Blueprint source:   %PROJECT_DIR%\blueprint\src\content.tex
  echo   Blueprint HTML:     %PROJECT_DIR%\blueprint\web\index.html
  echo   DAG output:         %PROJECT_DIR%\build\qedesk-dag.json
  echo   Mermaid DAG:        %PROJECT_DIR%\build\qedesk-dag.mmd
  echo   Cost ledger:        %PROJECT_DIR%\build\qedesk-ledger.sqlite
  echo.
  echo src\main.tex remains the student-facing source of truth.
  echo qedesk sync regenerates Blueprint source and the DAG sidecar from src\Proof.lean.
  exit /b 0
)
if "%COMMAND%"=="sync" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_sync.py
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="blueprint" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_sync.py
  if errorlevel 1 exit /b %ERRORLEVEL%
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" leanblueprint web
  if errorlevel 1 exit /b %ERRORLEVEL%
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_blueprint_ui.py
  if errorlevel 1 exit /b %ERRORLEVEL%
  echo.
  echo Blueprint HTML written to: %PROJECT_DIR%\blueprint\web\index.html
  echo Dependency graph written to: %PROJECT_DIR%\blueprint\web\dep_graph_document.html
  echo.
  echo To view it through the upstream Lean Blueprint server:
  echo   bin\qedesk.bat serve
  exit /b 0
)
if "%COMMAND%"=="serve" (
  if not exist "%PROJECT_DIR%\blueprint\web\index.html" (
    docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_sync.py
    if errorlevel 1 exit /b %ERRORLEVEL%
    docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" leanblueprint web
    if errorlevel 1 exit /b %ERRORLEVEL%
    docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_blueprint_ui.py
    if errorlevel 1 exit /b %ERRORLEVEL%
  )
  if not exist "%PROJECT_DIR%\blueprint\web\dep_graph_document.html" (
    docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_sync.py
    if errorlevel 1 exit /b %ERRORLEVEL%
    docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" leanblueprint web
    if errorlevel 1 exit /b %ERRORLEVEL%
    docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_blueprint_ui.py
    if errorlevel 1 exit /b %ERRORLEVEL%
  )
  echo Serving Blueprint at http://localhost:8000/
  echo Dependency graph: http://localhost:8000/dep_graph_document.html
  docker compose --project-directory "%PROJECT_DIR%" exec "%SERVICE%" leanblueprint serve
  exit /b 0
)
if "%COMMAND%"=="prepare" (
  docker compose --project-directory "%PROJECT_DIR%" exec "%SERVICE%" lake build Proof
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="cache" (
  docker compose --project-directory "%PROJECT_DIR%" exec "%SERVICE%" lake exe cache get
  exit /b %ERRORLEVEL%
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
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" lean-lsp-mcp
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="audit" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_router.py %*
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="formalize" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_router.py %*
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="repair" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_router.py %*
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="route" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_router.py %*
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="cost" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_router.py %*
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="init-ledger" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" python tools/qedesk_router.py %*
  exit /b %ERRORLEVEL%
)
if "%COMMAND%"=="clean" (
  docker compose --project-directory "%PROJECT_DIR%" exec -T "%SERVICE%" sh -lc "find %PDF_BUILD_DIR% -mindepth 1 ! -name qedesk-ledger.sqlite -delete 2>/dev/null || true; rm -rf _minted-* *.aux *.fdb_latexmk *.fls *.log *.out *.pdf blueprint/web blueprint/lean_decls blueprint/src/*.paux" 2>nul
  if errorlevel 1 powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%PROJECT_DIR%'; if (Test-Path '%PDF_BUILD_DIR%') { Get-ChildItem -LiteralPath '%PDF_BUILD_DIR%' -Force | Where-Object { $_.Name -ne 'qedesk-ledger.sqlite' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '_minted-*', '*.aux', '*.fdb_latexmk', '*.fls', '*.log', '*.out', '*.pdf', 'blueprint\web', 'blueprint\lean_decls', 'blueprint\src\*.paux'"
  exit /b 0
)
if "%COMMAND%"=="cost-reset" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-Item -LiteralPath '%PROJECT_DIR%\%PDF_BUILD_DIR%\qedesk-ledger.sqlite' -Force -ErrorAction SilentlyContinue"
  exit /b 0
)
if "%COMMAND%"=="docker-clean" (
  docker compose --project-directory "%PROJECT_DIR%" down --remove-orphans --volumes
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
echo   contracts     Show QEDesk v0.2 data-contract files
echo   sync          Sync Lean declarations into TeX, blueprint, and DAG files
echo   blueprint     Build the Lean Blueprint HTML visualization
echo   serve         Serve the generated Blueprint and dependency graph
echo   prepare       Build Lean once before launching MCP/OpenCode
echo   cache         Fetch Mathlib/Lean dependency cache when available
echo   lean          Build the Lean library
echo   build-lean    Alias for lean
echo   pdf           Build build/main.pdf from src/main.tex
echo   agent         Run lean-lsp-mcp inside the container
echo   audit         Audit QEDesk nodes through the OpenRouter router
echo   formalize     Ask the router for local Lean statements or skeletons
echo   repair        Ask the router for a local repair hint from a Lean error
echo   route         Show the model tier selected for a node
echo   cost          Show the OpenRouter cost ledger summary
echo   init-ledger   Create the local cost ledger database
echo   clean         Remove local build artifacts
echo   cost-reset    Remove the local OpenRouter cost ledger
echo   docker-clean  Remove the local QEDesk container and image
exit /b 0

:help_error
call :help
exit /b 2
