"""
Dashboard GET endpoints — AC1 through AC8 of issue #50.

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
from neo4j_client import driver as neo4j_driver

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env", override=True, encoding="utf-8-sig")

router = APIRouter(prefix="/api/v1", tags=["dashboard"])

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = 60  #seconds


def _risk_label(score: int) -> str:
    """Map a numeric risk score to a human-readable label."""
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


async def _redis_get(key: str):
    """Return cached JSON value for *key*, or None on miss/error."""
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None
    finally:
        await r.aclose()


async def _redis_set(key: str, value: dict) -> None:
    """Cache *value* under *key* for CACHE_TTL seconds."""
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.setex(key, CACHE_TTL, json.dumps(value))
    except Exception:
        pass  # cache failure must not break the response
    finally:
        await r.aclose()


def _cutoff_for_range(range_param: str) -> datetime | None:
    """Return the earliest timestamp to include, or None for 'all'."""
    now = datetime.now(timezone.utc)
    if range_param == "30d":
        return now - timedelta(days=30)
    if range_param == "90d":
        return now - timedelta(days=90)
    return None  # "all"


# AC1 — GET /api/v1/users/{user_id}/dashboard

@router.get("/users/{user_id}/dashboard")
async def get_dashboard(
    user_id: str,
    _current_user: str = Depends(get_current_user),  # AC6
):
    """
    Aggregated dashboard state: risk score, risk label, active alerts,
    and vulnerability profile summary.
    """
    cache_key = f"dashboard:{user_id}"
    cached = await _redis_get(cache_key)
    if cached is not None:  # AC7 cache hit
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

    # defaults for new/unknown users
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


# AC2 — GET /api/v1/users/{user_id}/profile

@router.get("/users/{user_id}/profile")
async def get_profile(
    user_id: str,
    _current_user: str = Depends(get_current_user),
):
    """
    User's dominant cognitive trait and all four bias scores from Neo4j.
    """
    cache_key = f"profile:{user_id}"
    cached = await _redis_get(cache_key)
    if cached is not None:  # cache hit
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

    # Build a lookup keyed by trigger name
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
    # If all scores are 0 the user has no data yet
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


# AC3 — GET /api/v1/users/{user_id}/risk-history?range={30d|90d|all}

@router.get("/users/{user_id}/risk-history")
async def get_risk_history(
    user_id: str,
    range: Literal["30d", "90d", "all"] = Query(default="30d"),
    _current_user: str = Depends(get_current_user),  # AC6
):
    """
    Array of ScoreDataPoints for the requested time window.
    """
    cutoff = _cutoff_for_range(range)

    with neo4j_driver.session() as session:
        if cutoff is not None:
            result = session.run(
                """
                MATCH (u:User {user_id: $uid})-[:HAS_SCORE_HISTORY]->(h:ScoreHistory)
                WHERE h.recorded_at >= $cutoff
                RETURN h.score AS score, h.recorded_at AS recorded_at
                ORDER BY h.recorded_at ASC
                """,
                uid=user_id,
                cutoff=cutoff.isoformat(),
            )
        else:
            result = session.run(
                """
                MATCH (u:User {user_id: $uid})-[:HAS_SCORE_HISTORY]->(h:ScoreHistory)
                RETURN h.score AS score, h.recorded_at AS recorded_at
                ORDER BY h.recorded_at ASC
                """,
                uid=user_id,
            )
        records = result.data()

    # empty history for new users
    data_points = [
        {"score": int(r["score"]), "timestamp": r["recorded_at"]}
        for r in records
        if r["score"] is not None and r["recorded_at"] is not None
    ]

    return {
        "user_id": user_id,
        "range": range,
        "data_points": data_points,
    }


# AC4 — GET /api/v1/users/{user_id}/training

@router.get("/users/{user_id}/training")
async def get_user_training(
    user_id: str,
    _current_user: str = Depends(get_current_user),  
):
    """
    List of training modules assigned to the user with progress,
    due dates, and completion status.
    """
    with neo4j_driver.session() as session:
        result = session.run(
            """
            OPTIONAL MATCH (u:User {user_id: $uid})-[a:ASSIGNED_TRAINING]->(m:TrainingModule)
            RETURN
                m.module_id         AS module_id,
                m.title             AS title,
                m.bias_target       AS bias_target,
                m.estimated_duration AS estimated_duration,
                a.progress          AS progress,
                a.due_date          AS due_date,
                a.completed         AS completed
            ORDER BY a.due_date ASC
            """,
            uid=user_id,
        )
        records = result.data()

    # new users have no assignments → return empty list
    modules = []
    for r in records:
        if r["module_id"] is None:
            continue
        modules.append(
            {
                "module_id": r["module_id"],
                "title": r["title"] or "Untitled Module",
                "bias_target": r["bias_target"] or "General",
                "estimated_duration": r["estimated_duration"] or 0,
                "progress": float(r["progress"]) if r["progress"] is not None else 0.0,
                "due_date": r["due_date"],
                "completed": bool(r["completed"]) if r["completed"] is not None else False,
            }
        )

    return {"user_id": user_id, "modules": modules}


# AC5 — GET /api/v1/training/{module_id}

@router.get("/training/{module_id}")
async def get_training_module(
    module_id: str,
    _current_user: str = Depends(get_current_user), 
):
    """
    Title, content URL, bias target, and estimated duration for one module.
    """
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (m:TrainingModule {module_id: $module_id})
            RETURN
                m.module_id          AS module_id,
                m.title              AS title,
                m.content_url        AS content_url,
                m.bias_target        AS bias_target,
                m.estimated_duration AS estimated_duration
            """,
            module_id=module_id,
        )
        record = result.single()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training module '{module_id}' not found.",
        )

    return {
        "module_id": record["module_id"],
        "title": record["title"] or "Untitled Module",
        "content_url": record["content_url"],
        "bias_target": record["bias_target"] or "General",
        "estimated_duration": record["estimated_duration"] or 0,
    }
