@echo off
REM Run winapp GUI or CLI
if "%1"=="gui" (
    python -c "from amatak_winapp.winapp import launch_gui; launch_gui()"
) else (
    python -m amatak_winapp.winapp %*
)