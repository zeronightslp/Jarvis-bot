import asyncio
import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("🔌 [WebSocket] Extensão do Navegador conectada!")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print("🔌 [WebSocket] Extensão do Navegador desconectada.")

    async def broadcast_command(self, action: str, target: str = "", value: str = ""):
        message = json.dumps({"action": action, "target": target, "value": value})
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"⚠️ [WebSocket] Erro ao enviar comando: {e}")
        
        if not self.active_connections:
            print("⚠️ [WebSocket] Nenhuma extensão conectada para receber o comando.")

manager = ConnectionManager()
