@echo off
echo Starting Blog Generation Agent...
echo.

:: Start Backend in a new window
echo Starting FastAPI Backend on port 8000...
start cmd /k ".venv\Scripts\activate && python server.py"

:: Start Frontend in a new window
echo Starting React Frontend...
cd frontend
start cmd /k "npm run dev"

echo.
echo Both servers are starting!
echo The backend API will be available at http://localhost:8000
echo The frontend UI will automatically open in your browser (usually http://localhost:5173).
