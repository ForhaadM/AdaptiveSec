from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True, encoding='utf-8-sig')

URI = os.getenv("NEO4J_URI", "")
USERNAME = os.getenv("NEO4J_USERNAME", "")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

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
    Google ID (sub) along with the user's email and display name (AC3)."""
    with driver.session() as session:
        session.run("""
            MERGE (u:User {user_id: $user_id})
            SET u.email = $email, u.display_name = $display_name
        """, user_id=user_id, email=email, display_name=display_name)
    
if __name__ == "__main__":
    init_schema()
    test_vulnerable_to_edge("agent_alex_001", "Urgency", 0.85)
    test_assigned_training_edge("agent_alex_001", "TM-URG-01")
    read_user_profile("agent_alex_001")