from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True, encoding='utf-8-sig')

URI = os.getenv("NEO4J_URI", "")
USERNAME = os.getenv("NEO4J_USERNAME", "")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD), max_connection_lifetime=200, keep_alive=True)

def init_schema():
    with driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:CognitiveTrigger) REQUIRE t.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:TrainingModule) REQUIRE m.module_id IS UNIQUE")
        session.run("MERGE (:CognitiveTrigger {name: 'Urgency'})")
        session.run("MERGE (:CognitiveTrigger {name: 'Authority'})")
        session.run("MERGE (:CognitiveTrigger {name: 'Scarcity'})")
        session.run("MERGE (:CognitiveTrigger {name: 'Social Proof'})")
        print("Schema initialized successfully")

def increment_video_index(user_id: str, module_id: str):
    """Increment video_index on ASSIGNED_TRAINING edge, max 2 (0,1,2 for 3 videos)."""
    with driver.session() as session:
        session.run("""
            MATCH (u:User {user_id: $user_id})-[r:ASSIGNED_TRAINING]->(m:TrainingModule {module_id: $module_id})
            SET r.video_index = CASE
                WHEN coalesce(r.video_index, 0) >= 2 THEN 2
                ELSE coalesce(r.video_index, 0) + 1
            END
        """, user_id=user_id, module_id=module_id)
        print(f"[Neo4j] Incremented video_index for {user_id} -> {module_id}")

def test_vulnerable_to_edge(user_id: str, trigger: str, bias_score: float):
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            MERGE (t:CognitiveTrigger {name: $trigger})
            MERGE (u)-[r:VULNERABLE_TO]->(t)
            SET r.bias_score = $bias_score
        """, user_id=user_id, trigger=trigger, bias_score=bias_score)
        print(f"VULNERABLE_TO edge created: {user_id} -> {trigger} ({bias_score})")

def test_assigned_training_edge(user_id: str, module_id: str):
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            MERGE (m:TrainingModule {module_id: $module_id})
            MERGE (u)-[:ASSIGNED_TRAINING]->(m)
        """, user_id=user_id, module_id=module_id)
        print(f"ASSIGNED_TRAINING edge created: {user_id} -> {module_id}")

def read_user_profile(user_id: str):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {user_id: $user_id})-[r:VULNERABLE_TO]->(t:CognitiveTrigger)
            RETURN t.name AS trigger, r.bias_score AS score
            ORDER BY score DESC
        """, user_id=user_id)
        records = result.data()
        print(f"Profile for {user_id}: {records}")
        return records

def update_trigger_weight(user_id: str, trigger: str):
    schema_map = {
        "Urgency_Bias": "Urgency",
        "Authority_Bias": "Authority",
        "Scarcity_Bias": "Scarcity",
        "Social_Proof_Bias": "Social Proof"
    }
    schema_trigger = schema_map.get(trigger, trigger)
    
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            MERGE (t:CognitiveTrigger {name: $trigger})
            MERGE (u)-[r:VULNERABLE_TO]->(t)
            SET r.bias_score = coalesce(r.bias_score, 0) + 1.0
        """, user_id=user_id, trigger=schema_trigger)
        print(f"Updated trigger weight for {user_id}: {schema_trigger}")

def get_dominant_cognitive_trigger(user_id: str) -> str | None:
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {user_id: $user_id})-[r:VULNERABLE_TO]->(t:CognitiveTrigger)
            WHERE t.name IN ['Urgency', 'Authority', 'Scarcity', 'Social Proof']
            WITH u, sum(r.bias_score) AS total_score
            WHERE total_score >= 3.0
            MATCH (u)-[r:VULNERABLE_TO]->(t:CognitiveTrigger)
            WHERE t.name IN ['Urgency', 'Authority', 'Scarcity', 'Social Proof']
            RETURN t.name AS trigger, r.bias_score AS score
            ORDER BY score DESC
            LIMIT 1
        """, user_id=user_id)
        record = result.single()
        return record["trigger"] if record else None

def store_explanation(event_id: str, user_id: str, explanation: str, cognitive_trigger: str):
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            MERGE (e:ClickEvent {event_id: $event_id})
            SET e.explanation = $explanation,
                e.cognitive_trigger = $cognitive_trigger,
                e.created_at = datetime()
            MERGE (u)-[:HAS_EVENT]->(e)
        """, event_id=event_id, user_id=user_id,
             explanation=explanation, cognitive_trigger=cognitive_trigger)

def get_explanation(event_id: str) -> str | None:
    with driver.session() as session:
        result = session.run("""
            MATCH (e:ClickEvent {event_id: $event_id})
            RETURN e.explanation AS explanation
        """, event_id=event_id)
        record = result.single()
        return record["explanation"] if record else None

def upsert_user(user_id: str, email: str = "", display_name: str = ""):
    """Create or update a User node. Used after Google OAuth to persist the
    Google ID (sub) along with the user's email and display name."""
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            SET u.email = $email, u.display_name = $display_name
        """, user_id=user_id, email=email, display_name=display_name)

def assign_training_module(user_id: str, module_id: str, due_date: str):
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            MERGE (m:TrainingModule {module_id: $module_id})
            MERGE (u)-[r:ASSIGNED_TRAINING]->(m)
            SET r.due_date = $due_date,
                r.status = 'incomplete',
                r.assigned_at = datetime()
        """, user_id=user_id, module_id=module_id, due_date=due_date)
        print(f"ASSIGNED_TRAINING edge created: {user_id} -> {module_id} | due={due_date}")

def get_active_assignment(user_id: str, trigger_name: str) -> str | None:
    trigger_to_module = {
        "Urgency":      "TM-URG-01",
        "Authority":    "TM-AUT-01",
        "Scarcity":     "TM-SCA-01",
        "Social Proof": "TM-SOC-01",
    }
    module_id = trigger_to_module.get(trigger_name)
    if not module_id:
        return None

    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {user_id: $user_id})-[r:ASSIGNED_TRAINING]->(m:TrainingModule {module_id: $module_id})
            WHERE r.status = 'incomplete'
            RETURN m.module_id AS module_id
        """, user_id=user_id, module_id=module_id)
        record = result.single()
        return record["module_id"] if record else None

# Risk Score Persistence

def persist_risk_score(user_id: str, risk_score: float):
    """Set current risk_score on User node."""
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            SET u.risk_score = $risk_score,
                u.score_updated_at = datetime()
        """, user_id=user_id, risk_score=risk_score)
        print(f"[Neo4j] Persisted risk_score={risk_score} for {user_id}")

def create_score_history(user_id: str, score: float, delta: float, reason: str):
    """Create a ScoreHistory node linked via HAS_SCORE_HISTORY."""
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            CREATE (h:ScoreHistory {
                score: $score,
                delta: $delta,
                reason: $reason,
                timestamp: datetime()
            })
            CREATE (u)-[:HAS_SCORE_HISTORY]->(h)
        """, user_id=user_id, score=score, delta=delta, reason=reason)
        print(f"[Neo4j] ScoreHistory created for {user_id}: score={score} delta={delta}")

def get_risk_score(user_id: str) -> float:
    """Read current risk_score from User node."""
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {user_id: $user_id})
            RETURN u.risk_score AS risk_score
        """, user_id=user_id)
        record = result.single()
        return float(record["risk_score"]) if record and record["risk_score"] is not None else 0.0

def get_score_history(user_id: str, range_days: int = 30) -> list:
    """Return ScoreHistory nodes within the requested time window."""
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {user_id: $user_id})-[:HAS_SCORE_HISTORY]->(h:ScoreHistory)
            WHERE h.timestamp >= datetime() - duration({days: $range_days})
            RETURN h.score AS score, h.delta AS delta,
                   h.reason AS reason, toString(h.timestamp) AS timestamp
            ORDER BY h.timestamp DESC
        """, user_id=user_id, range_days=range_days)
        return result.data()

# TrainingModule Queries 

def get_training_module(module_id: str) -> dict | None:
    """Return full metadata for a TrainingModule node."""
    with driver.session() as session:
        result = session.run("""
            MATCH (m:TrainingModule {module_id: $module_id})
            RETURN m.module_id AS module_id, m.title AS title,
                   m.video_urls AS video_urls, m.bias_target AS bias_target,
                   m.duration_seconds AS duration_seconds
        """, module_id=module_id)
        record = result.single()
        return dict(record) if record else None

def get_user_training(user_id: str) -> list:
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {user_id: $user_id})-[r:ASSIGNED_TRAINING]->(m:TrainingModule)
            RETURN m.module_id AS module_id, m.title AS title,
                   m.video_urls AS video_urls, m.bias_target AS bias_target,
                   m.duration_seconds AS duration_seconds,
                   r.status AS status, r.due_date AS due_date,
                   coalesce(r.video_index, 0) AS video_index,
                   coalesce(r.progress, 0) AS progress,
                   coalesce(r.completed, false) AS completed
            ORDER BY r.assigned_at DESC
        """, user_id=user_id)
        return result.data()

if __name__ == "__main__":
    init_schema()
    test_vulnerable_to_edge("agent_alex_001", "Urgency", 0.85)
    test_assigned_training_edge("agent_alex_001", "TM-URG-01")
    read_user_profile("agent_alex_001")