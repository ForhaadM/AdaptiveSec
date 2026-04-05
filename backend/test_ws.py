import asyncio
import websockets

async def t():
    uri = "ws://localhost:8000/ws/v1/alerts/testuser?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc3NDk5NzMyNn0.zIPJGDhHh-J1O8cS_-htVJPUXMlxvRZyUI25kBT2Kqo"
    async with websockets.connect(uri) as ws:
        print("connected")
        msg = await ws.recv()
        print("received:", msg)

asyncio.run(t())