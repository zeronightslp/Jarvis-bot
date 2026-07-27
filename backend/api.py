from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from jarvis import process_voice_command

app = FastAPI()

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
