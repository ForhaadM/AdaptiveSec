"""
Dashboard GET endpoints — W4-007 (AC1–AC8) + W4-005 completion endpoint.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query, status

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import get_current_user
from neo4j_client import driver as neo4j_driver, persist_risk_score, create_score_history

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env", override=True, encoding="utf-8-sig")

router = APIRouter(prefix="/api/v1", tags=["dashboard"])

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = 60  # seconds
TRAINING_SCORE_REDUCTION = 5.0  # pts deducted per completed module


def _risk_label(score: int) -> str:
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


async def _redis_get(key: str):
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None
    finally:
        await r.aclose()


async def _redis_set(key: str, value: dict) -> None:
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.setex(key, CACHE_TTL, json.dumps(value))
    except Exception:
        pass
    finally:
        await r.aclose()


async def _redis_delete(key: str) -> None:
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.delete(key)
    except Exception:
        pass
    finally:
        await r.aclose()


def _cutoff_for_range(range_param: str) -> datetime | None:
    now = datetime.now(timezone.utc)
    if range_param == "30d":
        return now - timedelta(days=30)
    if range_param == "90d":
        return now - timedelta(days=90)
    return None  # "all"




@router.get("/users/{user_id}/dashboard")
async def get_dashboard(
    user_id: str,
    _current_user: str = Depends(get_current_user),
):
    """Aggregated dashboard state: risk score, risk label, active alerts, vulnerability profile."""
    cache_key = f"dashboard:{user_id}"
    cached = await _redis_get(cache_key)
    if cached is not None:
        return cached

    with neo4j_driver.session() as session:
        result = session.run(
            """
            OPTIONAL MATCH (u:User {user_id: $uid})
            OPTIONAL MATCH (u)-[r:VULNERABLE_TO]->(t:CognitiveTrigger)
            RETURN
                u.risk_score       AS risk_score,
                u.active_alerts    AS active_alerts,
                collect(
                    CASE WHEN t IS NOT NULL
                         THEN {trigger: t.name, bias_score: r.bias_score}
                         ELSE null
                    END
                ) AS vulnerabilities
            """,
            uid=user_id,
        )
        record = result.single()

    risk_score = int(record["risk_score"]) if record and record["risk_score"] is not None else 0
    active_alerts = int(record["active_alerts"]) if record and record["active_alerts"] is not None else 0
    vulnerabilities = [
        v for v in (record["vulnerabilities"] if record else []) if v is not None
    ]

    payload = {
        "user_id": user_id,
        "risk_score": risk_score,
        "risk_label": _risk_label(risk_score),
        "active_alerts": active_alerts,
        "vulnerability_profile_summary": vulnerabilities,
    }

    await _redis_set(cache_key, payload)
    return payload




@router.get("/users/{user_id}/profile")
async def get_profile(
    user_id: str,
    _current_user: str = Depends(get_current_user),
):
    """User's dominant cognitive trait and all four bias scores from Neo4j."""
    cache_key = f"profile:{user_id}"
    cached = await _redis_get(cache_key)
    if cached is not None:
        return cached

    with neo4j_driver.session() as session:
        result = session.run(
            """
            OPTIONAL MATCH (u:User {user_id: $uid})-[r:VULNERABLE_TO]->(t:CognitiveTrigger)
            RETURN t.name AS trigger, r.bias_score AS score
            ORDER BY score DESC
            """,
            uid=user_id,
        )
        records = result.data()

    bias_map: dict[str, float] = {
        "Urgency": 0.0,
        "Authority": 0.0,
        "Scarcity": 0.0,
        "Social Proof": 0.0,
    }
    for row in records:
        if row["trigger"] in bias_map and row["score"] is not None:
            bias_map[row["trigger"]] = round(float(row["score"]), 4)

    dominant_trait = max(bias_map, key=bias_map.__getitem__)
    if all(v == 0.0 for v in bias_map.values()):
        dominant_trait = None

    payload = {
        "user_id": user_id,
        "dominant_cognitive_trait": dominant_trait,
        "bias_scores": {
            "Urgency": bias_map["Urgency"],
            "Authority": bias_map["Authority"],
            "Scarcity": bias_map["Scarcity"],
            "SocialProof": bias_map["Social Proof"],
        },
    }

    await _redis_set(cache_key, payload)
    return payload




@router.get("/users/{user_id}/risk-history")
async def get_risk_history(
    user_id: str,
    range: Literal["30d", "90d", "all"] = Query(default="30d"),
    _current_user: str = Depends(get_current_user),
):
    """Array of ScoreDataPoints (with delta and reason) for the requested time window."""
    cutoff = _cutoff_for_range(range)

    with neo4j_driver.session() as session:
        if cutoff is not None:
            result = session.run(
                """
                MATCH (u:User {user_id: $uid})-[:HAS_SCORE_HISTORY]->(h:ScoreHistory)
                WHERE h.timestamp >= $cutoff
                RETURN h.score      AS score,
                       h.delta      AS delta,
                       h.reason     AS reason,
                       toString(h.timestamp) AS timestamp
                ORDER BY h.timestamp ASC
                """,
                uid=user_id,
                cutoff=cutoff,
            )
        else:
            result = session.run(
                """
                MATCH (u:User {user_id: $uid})-[:HAS_SCORE_HISTORY]->(h:ScoreHistory)
                RETURN h.score      AS score,
                       h.delta      AS delta,
                       h.reason     AS reason,
                       toString(h.timestamp) AS timestamp
                ORDER BY h.timestamp ASC
                """,
                uid=user_id,
            )
        records = result.data()

    data_points = [
        {
            "score": int(r["score"]),
            "delta": float(r["delta"]) if r["delta"] is not None else 0.0,
            "reason": r["reason"] or "",
            "timestamp": r["timestamp"],
        }
        for r in records
        if r["score"] is not None and r["timestamp"] is not None
    ]

    return {
        "user_id": user_id,
        "range": range,
        "data_points": data_points,
    }




@router.get("/users/{user_id}/training")
async def get_user_training(
    user_id: str,
    _current_user: str = Depends(get_current_user),
):
    """List of training modules assigned to the user with progress, due dates, and completion status."""
    with neo4j_driver.session() as session:
        result = session.run(
            """
            OPTIONAL MATCH (u:User {user_id: $uid})-[a:ASSIGNED_TRAINING]->(m:TrainingModule)
            RETURN
                m.module_id        AS module_id,
                m.title            AS title,
                m.bias_target      AS bias_target,
                m.duration_seconds AS duration_seconds,
                a.progress         AS progress,
                a.due_date         AS due_date,
                a.completed        AS completed
            ORDER BY a.due_date ASC
            """,
            uid=user_id,
        )
        records = result.data()

    modules = []
    for r in records:
        if r["module_id"] is None:
            continue
        modules.append(
            {
                "module_id": r["module_id"],
                "title": r["title"] or "Untitled Module",
                "bias_target": r["bias_target"] or "General",
                "duration_seconds": r["duration_seconds"] or 0,
                "progress": float(r["progress"]) if r["progress"] is not None else 0.0,
                "due_date": r["due_date"],
                "completed": bool(r["completed"]) if r["completed"] is not None else False,
            }
        )

    return {"user_id": user_id, "modules": modules}




@router.get("/training/{module_id}")
async def get_training_module(
    module_id: str,
    _current_user: str = Depends(get_current_user),
):
    """Title, video URLs, bias target, and duration for one module."""
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (m:TrainingModule {module_id: $module_id})
            RETURN
                m.module_id        AS module_id,
                m.title            AS title,
                m.content_url      AS content_url,
                m.video_urls       AS video_urls,
                m.bias_target      AS bias_target,
                m.duration_seconds AS duration_seconds
            """,
            module_id=module_id,
        )
        record = result.single()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training module '{module_id}' not found.",
        )

    video_urls = record["video_urls"] or []
    content_url = record["content_url"] or (video_urls[0] if video_urls else None)

    return {
        "module_id": record["module_id"],
        "title": record["title"] or "Untitled Module",
        "content_url": content_url,
        "video_urls": video_urls,
        "bias_target": record["bias_target"] or "General",
        "duration_seconds": record["duration_seconds"] or 0,
    }




@router.post("/users/{user_id}/training/{module_id}/complete")
async def complete_training_module(
    user_id: str,
    module_id: str,
    _current_user: str = Depends(get_current_user),
):
    """
    Mark a training module as complete, reduce the user's risk score by
    TRAINING_SCORE_REDUCTION pts, and record a ScoreHistory entry.
    """
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {user_id: $uid})-[r:ASSIGNED_TRAINING]->(m:TrainingModule {module_id: $mid})
            SET r.status       = 'completed',
                r.progress     = 100,
                r.completed    = true,
                r.completed_at = datetime()
            RETURN coalesce(u.risk_score, 0) AS current_score
            """,
            uid=user_id,
            mid=module_id,
        )
        record = result.single()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active assignment of '{module_id}' found for user '{user_id}'.",
        )

    current_score = float(record["current_score"])
    new_score = max(0.0, current_score - TRAINING_SCORE_REDUCTION)

    
    persist_risk_score(user_id, new_score)
    create_score_history(
        user_id=user_id,
        score=new_score,
        delta=-TRAINING_SCORE_REDUCTION,
        reason=f"training_completed:{module_id}",
    )

    
    await _redis_delete(f"dashboard:{user_id}")
    await _redis_delete(f"risk_score:{user_id}")

    return {
        "user_id": user_id,
        "module_id": module_id,
        "previous_score": current_score,
        "new_score": new_score,
        "score_reduction": TRAINING_SCORE_REDUCTION,
    }
