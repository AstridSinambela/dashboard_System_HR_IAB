# app/websocket_manager.py
from typing import List
from fastapi import WebSocket

active_connections: List[WebSocket] = []

async def connect(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

def disconnect(websocket: WebSocket):
    if websocket in active_connections:
        active_connections.remove(websocket)

async def broadcast(message: dict):
    disconnected = []
    for conn in active_connections:
        try:
            await conn.send_json(message)   # kirim ke semua, termasuk sender
        except Exception:
            disconnected.append(conn)

    for conn in disconnected:
        active_connections.remove(conn)
