import asyncio
from collections import deque
from time import sleep
from fastapi.routing import APIRouter
from fastapi.websockets import WebSocketDisconnect, WebSocket, WebSocketState
from moirai_engine.core.engine import Engine
from moirai_engine.utils.samples import hello_world, slow_hello_world

app = APIRouter(prefix="/moirai", tags=["Moirai"])


def listener(event):
    print(event)


e = Engine(listener=listener)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections.keys():
            self.active_connections[job_id] = []
        connections = self.active_connections[job_id]
        connections.append(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        connections = self.active_connections.get(job_id, [])
        connections.remove(websocket)

    async def broadcast(self, job_id: str, message: str):
        for connection in self.active_connections.get(job_id, []):
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/hello")
async def add_hello():
    e.start()
    job = slow_hello_world()
    e.add_job(job)
    return {"job_id": job.id}


@app.websocket("/{job_id}")
async def notifications(websocket: WebSocket, job_id: str):

    await manager.connect(job_id=job_id, websocket=websocket)
    try:
        e.add_listener(
            listener=lambda x: asyncio.run(manager.broadcast(job_id, x)), job_id=job_id
        )
        for x in e.get_notification_history(job_id):
            await manager.broadcast(job_id, x)

        keepGoing = True
        while keepGoing:
            data = await websocket.receive_text()
            await manager.broadcast(job_id, "[CLIENT] " + str(data))
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)
