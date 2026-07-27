#!/usr/bin/env bash
# Run the Jarvis FastAPI server exposing the /command endpoint
# Ensure dependencies are installed: pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8080
