import httpx
import asyncio
import random
import logging
import json
import websockets
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

PERSONAS = {
    "rushed_employee": {
        "urgency_susceptibility": 0.85,
        "authority_susceptibility": 0.40,
        "social_proof_susceptibility": 0.30,
        "scarcity_susceptibility": 0.60,
        "baseline_caution": 0.20,
        "fatigue_factor": 0.70,
    },
    "rule_follower": {
        "urgency_susceptibility": 0.30,
        "authority_susceptibility": 0.80,
        "social_proof_susceptibility": 0.35,
        "scarcity_susceptibility": 0.25,
        "baseline_caution": 0.40,
        "fatigue_factor": 0.40,
    },
    "social_user": {
        "urgency_susceptibility": 0.25,
        "authority_susceptibility": 0.30,
        "social_proof_susceptibility": 0.85,
        "scarcity_susceptibility": 0.45,
        "baseline_caution": 0.30,
        "fatigue_factor": 0.50,
    },
    "cautious_user": {
        "urgency_susceptibility": 0.15,
        "authority_susceptibility": 0.20,
        "social_proof_susceptibility": 0.15,
        "scarcity_susceptibility": 0.20,
        "baseline_caution": 0.85,
        "fatigue_factor": 0.10,
    },
    "vulnerable_user": {
        "urgency_susceptibility": 0.90,
        "authority_susceptibility": 0.85,
        "social_proof_susceptibility": 0.80,
        "scarcity_susceptibility": 0.75,
        "baseline_caution": 0.10,
        "fatigue_factor": 0.90,
    },
}

SIMULATIONS = [
    {
        "simulation_id": "SIM-001",
        "trigger_type": "urgency",
        "template": "Your password expires in 24 hours. Click here to reset it immediately.",
        "url": "http://adaptive-sec-sim/reset",
    },
    {
        "simulation_id": "SIM-002",
        "trigger_type": "authority",
        "template": "IT Department: Verify your credentials to maintain system access.",
        "url": "http://adaptive-sec-sim/it-verify",
    },
    {
        "simulation_id": "SIM-003",
        "trigger_type": "scarcity",
        "template": "Only 2 accounts remaining with full access. Claim yours now.",
        "url": "http://adaptive-sec-sim/claim",
    },
    {
        "simulation_id": "SIM-004",
        "trigger_type": "social_proof",
        "template": "Your colleagues have already updated their security settings. Join them.",
        "url": "http://adaptive-sec-sim/update",
    },
    {
        "simulation_id": "SIM-005",
        "trigger_type": "urgency",
        "template": "URGENT: Suspicious login detected. Verify your identity immediately.",
        "url": "http://adaptive-sec-sim/verify",
    },
]


class SyntheticAgent:
    def __init__(self, persona_name: str, user_id: str):
        self.persona_name = persona_name
        self.user_id = user_id
        self.profile = PERSONAS[persona_name].copy()
        self.risk_score = 50
        self.score_trajectory = [50]
        self.token = None
        self.ws = None

    async def authenticate(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/auth/token",
                params={"user_id": self.user_id}
            )
            self.token = resp.json()["access_token"]
            logger.info(f"[{self.persona_name}] Authenticated as {self.user_id}")

    async def connect_websocket(self):
        uri = f"{WS_URL}/ws/v1/alerts/{self.user_id}?token={self.token}"
        self.ws = await websockets.connect(uri)
        logger.info(f"[{self.persona_name}] WebSocket connected")

    async def wait_for_score_update(self, timeout: float = 10.0) -> dict | None:
        try:
            message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            payload = json.loads(message)
            if payload.get("event") == "risk_update":
                new_score = payload.get("new_score", self.risk_score)
                self.update_score(new_score)
                logger.info(
                    f"[{self.persona_name}] Score update received → "
                    f"new_score={new_score} "
                    f"change={payload.get('score_change')} "
                    f"training={payload.get('new_training_id')}"
                )
                return payload
        except asyncio.TimeoutError:
            logger.warning(
                f"[{self.persona_name}] No score update received within {timeout}s — "
                f"pipeline may not be fully wired yet"
            )
        return None

    async def close_websocket(self):
        if self.ws:
            await self.ws.close()

    def calculate_click_probability(self, trigger_type: str) -> float:
        susceptibility_key = f"{trigger_type}_susceptibility"
        trigger_susceptibility = self.profile.get(susceptibility_key, 0.0)
        baseline_caution = self.profile["baseline_caution"]
        fatigue_penalty = self.profile["fatigue_factor"]
        noise = random.uniform(-0.05, 0.05)

        probability = (
            trigger_susceptibility
            * (1 - baseline_caution)
            * (2 - fatigue_penalty)
            + noise
        )
        return max(0.0, min(1.0, probability))

    async def run_simulation(self, simulation: dict):
        trigger_type = simulation["trigger_type"]
        click_prob = self.calculate_click_probability(trigger_type)
        random_draw = random.random()
        clicked = random_draw < click_prob

        logger.info(
            f"[{self.persona_name}] SIM={simulation['simulation_id']} "
            f"trigger={trigger_type} prob={click_prob:.3f} draw={random_draw:.3f} "
            f"clicked={clicked}"
        )

        if clicked:
            await self.fire_telemetry(simulation)
            await self.wait_for_score_update()

    async def fire_telemetry(self, simulation: dict):
        payload = {
            "user_id": self.user_id,
            "simulation_id": simulation["simulation_id"],
            "trigger_type": simulation["trigger_type"],
            "url": simulation["url"],
            "page_context": simulation["template"],
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/telemetry/click",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            logger.info(
                f"[{self.persona_name}] Telemetry fired → {resp.status_code}"
            )

    def complete_training(self, trigger_type: str, learning_rate: float = 0.25):
        key = f"{trigger_type}_susceptibility"
        old = self.profile[key]
        self.profile[key] = old * (1 - learning_rate)
        logger.info(
            f"[{self.persona_name}] Training complete for {trigger_type} | "
            f"susceptibility {old:.3f} → {self.profile[key]:.3f}"
        )

    def relapse_after_click(self, trigger_type: str, click_penalty: float = 0.1):
        key = f"{trigger_type}_susceptibility"
        old = self.profile[key]
        self.profile[key] = old + (click_penalty * 0.5)
        logger.info(
            f"[{self.persona_name}] Relapse on {trigger_type} | "
            f"susceptibility {old:.3f} → {self.profile[key]:.3f}"
        )

    def update_score(self, new_score: int):
        self.risk_score = new_score
        self.score_trajectory.append(new_score)

    def log_trajectory(self):
        logger.info(
            f"[{self.persona_name}] Score trajectory: {self.score_trajectory}"
        )


async def run_all_agents():
    agents = [
        SyntheticAgent("rushed_employee",  "agent_rushed_001"),
        SyntheticAgent("rule_follower",    "agent_rule_001"),
        SyntheticAgent("social_user",      "agent_social_001"),
        SyntheticAgent("cautious_user",    "agent_cautious_001"),
        SyntheticAgent("vulnerable_user",  "agent_vulnerable_001"),
    ]

    for agent in agents:
        await agent.authenticate()

    
    for agent in agents:
        await agent.connect_websocket()

    # Run 5 simulation rounds per agent
    for round_num in range(1, 6):
        logger.info(f"\n--- Round {round_num} ---")
        for agent in agents:
            sim = random.choice(SIMULATIONS)
            await agent.run_simulation(sim)
            await asyncio.sleep(0.5)

    # Log trajectories
    for agent in agents:
        agent.log_trajectory()

    # Close WebSocket connections
    for agent in agents:
        await agent.close_websocket()


if __name__ == "__main__":
    asyncio.run(run_all_agents())