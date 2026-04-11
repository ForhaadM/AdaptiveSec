from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Query, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router, get_current_user, verify_token
from websocket_manager import manager
from routers.telemetry import router as telemetry_router
from neo4j_client import get_risk_score, get_score_history, get_training_module, get_user_training
import redis as sync_redis
import os

app = FastAPI(title="AdaptiveSec API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(telemetry_router)

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

# Risk Score Endpoints 

@app.get("/api/v1/users/{user_id}/dashboard")
async def get_dashboard(user_id: str, current_user: str = Depends(get_current_user)):
    """Return user's current risk score, Redis cached with 60s TTL."""
    r = sync_redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    cached = r.get(f"risk_score:{user_id}")
    if cached:
        risk_score = float(cached)
    else:
        risk_score = get_risk_score(user_id)
    return {"user_id": user_id, "risk_score": risk_score}

@app.get("/api/v1/users/{user_id}/risk-history")
async def get_risk_history(
    user_id: str,
    range: str = "30d",
    current_user: str = Depends(get_current_user)
):
    """Return ScoreHistory data points for the requested time window (30d, 90d, all)."""
    if range == "all":
        range_days = 36500
    else:
        range_days = int(range.replace("d", ""))
    history = get_score_history(user_id, range_days)
    return {"user_id": user_id, "range": range, "history": history}

#  Training Module Endpoints 

@app.get("/api/v1/training/{module_id}")
async def get_training_module_detail(
    module_id: str,
    current_user: str = Depends(get_current_user)
):
    """AC4 — Return full module metadata including title and video URLs."""
    module = get_training_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@app.get("/api/v1/users/{user_id}/training")
async def get_user_training_modules(
    user_id: str,
    current_user: str = Depends(get_current_user)
):
    """AC5 — Return assigned modules with full title and video URLs populated."""
    modules = get_user_training(user_id)
    return {"user_id": user_id, "modules": modules}