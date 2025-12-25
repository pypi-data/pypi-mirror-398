import os

def create_pyb_bat():
    """
    Erstellt im aktuellen Ordner PyB.bat
    """
    cwd = os.getcwd()
    bat_path = os.path.join(cwd, "PyB.bat")
    
    bat_content = r"""@echo off
REM ==========================================================
REM  Creative Commons Zero (CC0) License
REM ==========================================================
python -m twine --version >nul 2>&1

IF ERRORLEVEL 1 (
    echo echo Pyb installing TWINE
    python -m pip install --upgrade pip
    python -m pip install build twine
) ELSE (
    echo Pyb ready
)

if not exist "%cd%\pyb" mkdir "%cd%\pyb"
if not exist "%cd%\pyb\BuildFolder.pyb" echo Build> "%cd%\pyb\BuildFolder.pyb"
set /p BUILDFOLDER=<"%cd%\pyb\BuildFolder.pyb"
for /f "tokens=* delims= " %%a in ("%BUILDFOLDER%") do set BUILDFOLDER=%%a
:trimLoop
if "%BUILDFOLDER:~-1%"==" " set BUILDFOLDER=%BUILDFOLDER:~0,-1%& goto trimLoop
IF "%~1"=="" GOTO help

IF /I "%1"=="build"        GOTO build
IF /I "%1"=="test"         GOTO test
IF /I "%1"=="upload"       GOTO upload
IF /I "%1"=="upload-token" GOTO upload_token
IF /I "%1"=="version"      GOTO version_show

GOTO help

:build
echo Cleaning BUILD folder... ("%cd%\%BUILDFOLDER%")
if exist "%cd%\%BUILDFOLDER%" rmdir /s /q "%cd%\%BUILDFOLDER%"
python -m build --outdir "%cd%\%BUILDFOLDER%" > "%cd%\pyb\build.log" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Build Complete
) else (
    echo Error
    type "%cd%\pyb\build.log"
)
GOTO end

:test
pip install -e .
GOTO end

:upload
IF NOT exist "%cd%\pyb\Token.bd" GOTO make_token
IF NOT exist "%cd%\%BUILDFOLDER%"     GOTO build_for_upload
GOTO upload_with_file

:upload_token
IF NOT exist "%cd%\%BUILDFOLDER%" GOTO build_for_upload_token
GOTO upload_with_input

:upload_with_file
set /p TOKEN=< "%cd%\pyb\Token.bd"
python -m twine upload "%cd%\%BUILDFOLDER%\*" -u __token__ -p %TOKEN% > "%cd%\pyb\build.log" 2>&1 
if %ERRORLEVEL% EQU 0 (
    echo Upload Complete
) else (
    echo Error
    echo ---------------------------------
    type "%cd%\pyb\build.log"
    echo ---------------------------------
)
Goto end

:upload_with_input
set /p TOKEN=Enter your token: 
python -m twine upload "%cd%\%BUILDFOLDER%\*" -u __token__ -p %TOKEN% > "%cd%\pyb\build.log" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Upload Complete
) else (
    echo Error
    echo ---------------------------------
    type "%cd%\pyb\build.log"
    echo ---------------------------------
)
GOTO end

:make_token
echo Creating Token.bd file...
echo --ENTER YOUR TOKEN-- > "%cd%\pyb\Token.bd"
echo Token file created at: "%cd%\pyb\Token.bd"
GOTO end

:build_for_upload
python -m build --outdir "%cd%\%BUILDFOLDER%" > "%cd%\pyb\build.log" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Build Complete
) else (
    echo Error
    echo ---------------------------------
    type "%cd%\pyb\build.log"
    echo ---------------------------------
)
GOTO upload_with_file

:build_for_upload_token
python -m build --outdir "%cd%\%BUILDFOLDER%" > "%cd%\pyb\build.log" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Build Complete
) else (
    echo Error
    echo ---------------------------------
    type "%cd%\pyb\build.log"
    echo ---------------------------------
)
GOTO upload_token

:version_show
type setup.cfg | findstr version
goto end

:help
echo PyBd:
echo.
echo Usage:
echo   PyB build
echo     Build your package
echo.
echo   PyB test
echo     Install package locally for testing
echo.
echo   PyB upload
echo     Upload using saved token (Token.bd)
echo.
echo   PyB upload-token
echo     Upload by manually entering a token
echo.
echo   PyB version
echo     Show the version
echo.
:end
"""
    # Mit Windows-Zeilenenden und UTF-8 schreiben
    with open(bat_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(bat_content)

create_pyb_bat()
