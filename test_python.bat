@echo off
echo Testing Python installation...
python test_python.py
if errorlevel 1 (
  echo.
  echo Error running test_python.py
  echo.
  echo Please make sure Python is installed and in your PATH.
  echo You can download Python from https://www.python.org/downloads/
  echo.
  echo Trying alternative Python commands...
  echo.
  
  echo Trying py command...
  py test_python.py
  if errorlevel 1 (
    echo Trying python3 command...
    python3 test_python.py
    if errorlevel 1 (
      echo.
      echo Failed to run the test script.
      echo All standard Python commands failed.
      echo.
      echo Please make sure Python is installed properly and added to your PATH.
      echo.
    )
  )
)
pause