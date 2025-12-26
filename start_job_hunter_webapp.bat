@echo off
TITLE JOB HUNTER WEBAPP

call "%USERPROFILE%\anaconda3\Scripts\activate.bat"
call conda activate jobhunter

python app_04.py

pause
