from contextlib import asynccontextmanager
import asyncio
import os
import random
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Query, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router, get_current_user, verify_token
from websocket_manager import manager
from routers.telemetry import router as telemetry_router
from routers.dashboard import router as dashboard_router
from simulation_engine import simulation_engine
from neo4j_client import get_risk_score, read_user_profile, get_user_training, get_training_module, persist_risk_score, create_score_history
from rabbitmq_client import publish_event
import redis as sync_redis


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


# --- Admin Agent Endpoints (no auth) ---

AGENT_CLICK_PROBS = {
    "agent_cautious_001":   0.02,
    "agent_secure_001":     0.01,
    "agent_vulnerable_001": 1.00,
    "agent_rushed_001":     0.80,
    "agent_deadline_001":   0.75,
    "agent_manager_001":    0.70,
    "agent_rule_001":       0.72,
    "agent_compliance_001": 0.78,
    "agent_newhire_001":    0.74,
    "agent_social_001":     0.76,
    "agent_teamplayer_001": 0.71,
    "agent_fomo_001":       0.79,
    "agent_bargain_001":    0.73,
    "agent_hoarder_001":    0.77,
    "agent_remote_001":     0.68,
}

AGENT_SIMULATIONS = [
    {"simulation_id": "SIM-001", "trigger_type": "urgency",
     "template": "Your password expires in 24 hours. Click here to reset immediately.",
     "url": "http://adaptive-sec-sim/reset"},
    {"simulation_id": "SIM-002", "trigger_type": "authority",
     "template": "IT Department: Verify your credentials to maintain system access.",
     "url": "http://adaptive-sec-sim/it-verify"},
    {"simulation_id": "SIM-003", "trigger_type": "scarcity",
     "template": "Only 2 accounts remaining with full access. Claim yours now.",
     "url": "http://adaptive-sec-sim/claim"},
    {"simulation_id": "SIM-004", "trigger_type": "social_proof",
     "template": "Your colleagues have already updated their security settings. Join them.",
     "url": "http://adaptive-sec-sim/update"},
    {"simulation_id": "SIM-005", "trigger_type": "urgency",
     "template": "URGENT: Suspicious login detected. Verify your identity immediately.",
     "url": "http://adaptive-sec-sim/verify"},
]


@app.get("/api/v1/admin/agent-scores")
async def get_all_agent_scores():
    scores = {}
    for uid in AGENT_CLICK_PROBS:
        scores[uid] = get_risk_score(uid)
    return {"agents": scores}


@app.get("/api/v1/users/{user_id}/profile-public")
async def get_user_profile_public(user_id: str):
    """Cognitive vulnerability profile — no auth."""
    profile = read_user_profile(user_id)
    return {"user_id": user_id, "triggers": profile}


@app.get("/api/v1/admin/agent-history/{user_id}")
async def get_agent_history(user_id: str, range: str = "all"):
    """Risk score history for agent — no auth."""
    from neo4j_client import driver
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    if range == "30d":
        cutoff = now - timedelta(days=30)
    elif range == "90d":
        cutoff = now - timedelta(days=90)
    else:
        cutoff = None

    with driver.session() as session:
        if cutoff:
            result = session.run("""
                MATCH (u:User {user_id: $uid})-[:HAS_SCORE_HISTORY]->(h:ScoreHistory)
                WHERE h.timestamp >= $cutoff
                RETURN h.score AS score, h.delta AS delta,
                       h.reason AS reason, toString(h.timestamp) AS timestamp
                ORDER BY h.timestamp ASC
            """, uid=user_id, cutoff=cutoff)
        else:
            result = session.run("""
                MATCH (u:User {user_id: $uid})-[:HAS_SCORE_HISTORY]->(h:ScoreHistory)
                RETURN h.score AS score, h.delta AS delta,
                       h.reason AS reason, toString(h.timestamp) AS timestamp
                ORDER BY h.timestamp ASC
            """, uid=user_id)
        records = result.data()

    data_points = [
        {
            "score": int(r["score"]),
            "delta": float(r["delta"]) if r["delta"] is not None else 0.0,
            "reason": r["reason"] or "",
            "timestamp": r["timestamp"],
        }
        for r in records if r["score"] is not None
    ]
    return {"user_id": user_id, "range": range, "data_points": data_points}


@app.get("/api/v1/admin/agent-training/{user_id}")
async def get_agent_training(user_id: str):
    """Training modules for agent — no auth."""
    modules = get_user_training(user_id)
    return {"user_id": user_id, "modules": modules}


@app.get("/api/v1/admin/training/{module_id}")
async def get_training_module_public(module_id: str):
    """Return training module detail — no auth for agent viewer."""
    module = get_training_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@app.post("/api/v1/admin/run-simulation/{user_id}")
async def run_agent_simulation(user_id: str):
    sim = random.choice(AGENT_SIMULATIONS)
    base_prob = AGENT_CLICK_PROBS.get(user_id, 0.6)
    noise = random.gauss(0, 0.05)
    click_prob = max(0.0, min(1.0, base_prob + noise))
    clicked = random.random() < click_prob

    if not clicked:
        current = get_risk_score(user_id)
        if current > 0:
            new_score = max(0.0, current - 2.0)
            persist_risk_score(user_id, new_score)
            create_score_history(
                user_id=user_id,
                score=new_score,
                delta=-2.0,
                reason="skipped_phishing"
            )
            r = sync_redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
            r.delete(f"risk_score:{user_id}")
        return {"user_id": user_id, "simulation": sim, "status": "skipped", "clicked": False, "click_prob": round(click_prob, 3)}

    event = {
        "user_id": user_id,
        "simulation_id": sim["simulation_id"],
        "trigger_type": sim["trigger_type"],
        "url": sim["url"],
        "page_context": sim["template"],
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    publish_event(event)
    return {"user_id": user_id, "simulation": sim, "status": "fired", "clicked": True, "click_prob": round(click_prob, 3)}


@app.post("/api/v1/admin/reset-agents")
async def reset_all_agents():
    from neo4j_client import driver
    with driver.session() as session:
        session.run("MATCH (u:User) WHERE u.user_id STARTS WITH 'agent_' DETACH DELETE u")
    r = sync_redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    keys = r.keys("risk_score:agent_*")
    if keys:
        r.delete(*keys)
    return {"status": "cleared"}

@app.post("/api/v1/admin/agent-training/{user_id}/{module_id}/complete")
async def complete_agent_training(user_id: str, module_id: str):
    """Mark training complete for agent — no auth."""
    from neo4j_client import driver, persist_risk_score, create_score_history

    TRAINING_SCORE_REDUCTION = 5.0

    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {user_id: $uid})-[r:ASSIGNED_TRAINING]->(m:TrainingModule {module_id: $mid})
            WHERE r.completed IS NULL OR r.completed = false
            SET r.status = 'completed', r.progress = 100,
                r.completed = true, r.completed_at = datetime()
            RETURN coalesce(u.risk_score, 0) AS current_score
        """, uid=user_id, mid=module_id)
        record = result.single()

    if not record:
        raise HTTPException(status_code=404, detail="Assignment not found or already completed")

    current_score = float(record["current_score"])
    new_score = max(0.0, current_score - TRAINING_SCORE_REDUCTION)

    persist_risk_score(user_id, new_score)
    create_score_history(
        user_id=user_id, score=new_score,
        delta=-TRAINING_SCORE_REDUCTION,
        reason=f"training_completed:{module_id}"
    )

    r = sync_redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    r.delete(f"risk_score:{user_id}")

    return {"user_id": user_id, "module_id": module_id, "previous_score": current_score, "new_score": new_score}