@echo off
echo Running DAT Filter AI Simple Interactive CLI...
python simple_interactive.py %*
if errorlevel 1 (
  echo.
  echo Error running simple_interactive.py
  echo.
  echo Please make sure Python is installed and in your PATH.
  echo You can download Python from https://www.python.org/downloads/
  echo.
  echo Trying alternative Python commands...
  echo.
  
  echo Trying py command...
  py simple_interactive.py %*
  if errorlevel 1 (
    echo Trying python3 command...
    python3 simple_interactive.py %*
    if errorlevel 1 (
      echo.
      echo Failed to run the interactive script.
      echo.
      echo Please make sure Python is installed properly.
      echo.
    )
  )
)
pause