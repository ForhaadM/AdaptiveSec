"""
W4-008: Phishing Simulation Delivery Engine
Delivers simulated phishing attempts to connected users via WebSocket,
then publishes click events to RabbitMQ for the ML pipeline to process.
"""

import os
import json
import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SIMULATION_INTERVAL_SECONDS = int(os.getenv("SIMULATION_INTERVAL_SECONDS", 120))  # 2 min demo, 86400 prod

# 8 simulation templates, 2 per trigger type
SIMULATION_TEMPLATES = [
    {
        "simulation_id": "SIM-URG-01",
        "trigger_type": "urgency",
        "template_text": "⚠️ URGENT: Your account password expires in 10 minutes. Click here to reset it immediately or lose access.",
        "phishing_url": "http://secure-reset.adaptivesec-demo.com/reset?token=abc123",
    },
    {
        "simulation_id": "SIM-URG-02",
        "trigger_type": "urgency",
        "template_text": "Action Required: Your IT access will be revoked in 30 minutes due to a security policy update. Click to verify now.",
        "phishing_url": "http://it-verify.adaptivesec-demo.com/verify?id=xyz789",
    },
    {
        "simulation_id": "SIM-AUT-01",
        "trigger_type": "authority",
        "template_text": "Message from IT Department: Please update your credentials immediately to comply with the new security policy.",
        "phishing_url": "http://it-dept.adaptivesec-demo.com/update-credentials",
    },
    {
        "simulation_id": "SIM-AUT-02",
        "trigger_type": "authority",
        "template_text": "CEO Notice: All employees must complete this mandatory security verification by end of day.",
        "phishing_url": "http://ceo-notice.adaptivesec-demo.com/verify",
    },
    {
        "simulation_id": "SIM-SCA-01",
        "trigger_type": "scarcity",
        "template_text": "Only 2 spots left for the company security training session. Reserve your spot now before it's too late.",
        "phishing_url": "http://training-signup.adaptivesec-demo.com/reserve",
    },
    {
        "simulation_id": "SIM-SCA-02",
        "trigger_type": "scarcity",
        "template_text": "Limited offer: Your free cloud storage upgrade expires today. Click to claim your 50GB before midnight.",
        "phishing_url": "http://storage-upgrade.adaptivesec-demo.com/claim",
    },
    {
        "simulation_id": "SIM-SOC-01",
        "trigger_type": "social_proof",
        "template_text": "87 of your colleagues have already updated their security profile. Don't get left behind — update yours now.",
        "phishing_url": "http://profile-update.adaptivesec-demo.com/update",
    },
    {
        "simulation_id": "SIM-SOC-02",
        "trigger_type": "social_proof",
        "template_text": "Your team has completed the security survey. You're the only one who hasn't responded yet. Click to complete.",
        "phishing_url": "http://survey.adaptivesec-demo.com/complete",
    },
]


class SimulationEngine:

    def __init__(self):
        self.redis = None

    async def _get_redis(self):
        if not self.redis:
            self.redis = aioredis.from_url(REDIS_URL)
        return self.redis

    async def _get_last_simulation_time(self, user_id: str) -> Optional[datetime]:
        """AC3 — Check when the last simulation was delivered to this user."""
        r = await self._get_redis()
        val = await r.get(f"last_sim:{user_id}")
        if val:
            return datetime.fromisoformat(val.decode())
        return None

    async def _set_last_simulation_time(self, user_id: str):
        r = await self._get_redis()
        await r.set(f"last_sim:{user_id}", datetime.utcnow().isoformat())

    async def _get_shown_simulations(self, user_id: str) -> list:
        """AC6 — Get list of simulation_ids already shown to this user."""
        r = await self._get_redis()
        val = await r.get(f"shown_sims:{user_id}")
        if val:
            return json.loads(val.decode())
        return []

    async def _record_shown_simulation(self, user_id: str, simulation_id: str):
        """AC6 — Record that this simulation was shown to the user."""
        r = await self._get_redis()
        shown = await self._get_shown_simulations(user_id)
        if simulation_id not in shown:
            shown.append(simulation_id)
        # Reset if all simulations have been shown
        if len(shown) >= len(SIMULATION_TEMPLATES):
            shown = [simulation_id]
        await r.set(f"shown_sims:{user_id}", json.dumps(shown))

    def _pick_template(self, shown: list) -> dict:
        """AC6 — Pick a template not yet shown to this user."""
        available = [t for t in SIMULATION_TEMPLATES if t["simulation_id"] not in shown]
        if not available:
            available = SIMULATION_TEMPLATES  # reset cycle
        return random.choice(available)

    async def deliver_simulation(self, user_id: str, websocket_manager) -> bool:
        """
        AC2 — Deliver a simulation to the user via WebSocket.
        AC3 — Only deliver if interval has passed.
        AC6 — Never show the same simulation twice until all have been shown.
        Returns True if simulation was delivered.
        """
        # Check interval
        last_time = await self._get_last_simulation_time(user_id)
        if last_time:
            elapsed = (datetime.utcnow() - last_time).total_seconds()
            if elapsed < SIMULATION_INTERVAL_SECONDS:
                logger.debug(f"[SimEngine] Skipping {user_id} — {elapsed:.0f}s since last sim")
                return False

        # Pick unseen template
        shown = await self._get_shown_simulations(user_id)
        template = self._pick_template(shown)

        # Build and send WebSocket payload
        payload = {
            "event": "simulation_delivered",
            "simulation_id": template["simulation_id"],
            "trigger_type": template["trigger_type"],
            "template_text": template["template_text"],
            "phishing_url": template["phishing_url"],
            "delivered_at": datetime.utcnow().isoformat(),
        }

        try:
            ws = websocket_manager._connections.get(user_id)
            if not ws:
                logger.debug(f"[SimEngine] {user_id} not connected via WebSocket")
                return False

            await ws.send_json(payload)
            await self._set_last_simulation_time(user_id)
            await self._record_shown_simulation(user_id, template["simulation_id"])
            logger.info(f"[SimEngine] Delivered {template['simulation_id']} to {user_id}")
            return True

        except Exception as e:
            logger.warning(f"[SimEngine] Failed to deliver to {user_id}: {e}")
            return False

    async def run_delivery_loop(self, websocket_manager):
        """
        AC3 — Background loop that checks all connected users every 30s
        and delivers simulations on schedule.
        """
        logger.info(f"[SimEngine] Delivery loop started — interval={SIMULATION_INTERVAL_SECONDS}s")
        while True:
            await asyncio.sleep(30)  # check every 30s
            connected_users = list(websocket_manager._connections.keys())
            for user_id in connected_users:
                await self.deliver_simulation(user_id, websocket_manager)


simulation_engine = SimulationEngine()