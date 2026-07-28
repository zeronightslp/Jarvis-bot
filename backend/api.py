from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis import process_voice_command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Command(BaseModel):
    command: str

@app.post("/command")
async def run_command(payload: Command):
    try:
        # Forward the command string to the existing Jarvis processor
        process_voice_command(payload.command)
        return {"status": "ok", "message": f"Comando '{payload.command}' executado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
