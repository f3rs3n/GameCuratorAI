@echo off
echo Running DAT Filter AI local setup...
python setup_local.py
if errorlevel 1 (
  echo.
  echo Error running setup_local.py
  echo.
  echo Please make sure Python is installed and in your PATH.
  echo You can download Python from https://www.python.org/downloads/
  echo.
  echo Trying alternative Python commands...
  echo.
  
  echo Trying py command...
  py setup_local.py
  if errorlevel 1 (
    echo Trying python3 command...
    python3 setup_local.py
    if errorlevel 1 (
      echo.
      echo Failed to run the setup script.
      echo.
      echo Please make sure Python is installed properly.
      echo.
      echo You can also install dependencies manually with:
      echo.
      echo pip install colorama openai google-generativeai
      echo.
      echo For the GUI, you'll also need:
      echo pip install PyQt5
      echo.
    )
  )
)
pause