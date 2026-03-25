import asyncio
import websockets

async def t():
    uri = "ws://localhost:8000/ws/v1/alerts/testuser?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc3NDQ3OTcyNH0.F10D36y-u5J68btdWvqz69-XXqwk2IqjVGyHG0-b4Zo"
    async with websockets.connect(uri) as ws:
        print("connected")
        msg = await ws.recv()
        print("received:", msg)

asyncio.run(t())