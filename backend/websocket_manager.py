import asyncio
import json
from fastapi import WebSocket
import redis.asyncio as aioredis

REDIS_URL = "redis://localhost:6379"

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[user_id] = websocket
        task = asyncio.create_task(self._redis_listener(user_id, websocket))
        self._tasks[user_id] = task

    def disconnect(self, user_id: str):
        self._connections.pop(user_id, None)
        task = self._tasks.pop(user_id, None)
        if task:
            task.cancel()

    async def _redis_listener(self, user_id: str, websocket: WebSocket):
        r = aioredis.from_url(REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"alerts:{user_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    await websocket.send_json(payload)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(f"alerts:{user_id}")
            await r.aclose()

manager = ConnectionManager()