import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j_client import driver

def validate():
    with driver.session() as session:
        
        print("\n=== USER NODES ===")
        result = session.run("MATCH (u:User) RETURN u.user_id AS user_id")
        for r in result:
            print(f"  {r['user_id']}")

        print("\n=== VULNERABLE_TO EDGES ===")
        result = session.run("""
            MATCH (u:User)-[r:VULNERABLE_TO]->(t:CognitiveTrigger)
            RETURN u.user_id AS user_id, t.name AS trigger, r.bias_score AS score
            ORDER BY user_id, score DESC
        """)
        for r in result:
            print(f"  {r['user_id']} -> {r['trigger']} (score: {r['score']})")

        print("\n=== DOMINANT TRAITS ===")
        result = session.run("""
            MATCH (u:User)-[r:VULNERABLE_TO]->(t:CognitiveTrigger)
            WITH u.user_id AS user_id, t.name AS trigger, r.bias_score AS score
            ORDER BY user_id, score DESC
            WITH user_id, collect({trigger: trigger, score: score})[0] AS dominant
            RETURN user_id, dominant.trigger AS dominant_trigger, dominant.score AS score
        """)
        for r in result:
            print(f"  {r['user_id']} → dominant: {r['dominant_trigger']} (score: {r['score']})")

        print("\n=== ASSIGNED TRAINING EDGES ===")
        result = session.run("""
            MATCH (u:User)-[r:ASSIGNED_TRAINING]->(m:TrainingModule)
            RETURN u.user_id AS user_id, m.module_id AS module_id, 
                   r.status AS status, r.due_date AS due_date
        """)
        records = result.data()
        if records:
            for r in records:
                print(f"  {r['user_id']} -> {r['module_id']} status={r['status']}")
        else:
            print("  No training assignments yet")

if __name__ == "__main__":
    validate()