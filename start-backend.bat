@echo off
echo Starting Synapse Backend...
cd backend
call ..\synapsenv\Scripts\activate
python main.py
