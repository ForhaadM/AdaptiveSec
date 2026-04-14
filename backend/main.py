from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Query, status
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router, get_current_user, verify_token
from websocket_manager import manager
from routers.telemetry import router as telemetry_router
from routers.dashboard import router as dashboard_router
from simulation_engine import simulation_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(simulation_engine.run_delivery_loop(manager))
    yield


app = FastAPI(title="AdaptiveSec API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(telemetry_router)
app.include_router(dashboard_router)


@app.get("/protected")
async def protected_route(user_id: str = Depends(get_current_user)):
    return {"message": f"Hello {user_id}, you are authenticated"}


@app.websocket("/ws/v1/alerts/{user_id}")
async def websocket_alerts(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...)
):
    payload = verify_token(token)
    if not payload or payload.get("sub") != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)
