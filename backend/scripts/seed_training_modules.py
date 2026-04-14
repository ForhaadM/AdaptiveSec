"""
W4-012: Seed TrainingModule nodes in Neo4j
Run from backend/ directory: python scripts/seed_training_modules.py
Can be re-run safely — uses MERGE so no duplicates.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from neo4j_client import driver

TRAINING_MODULES = [
    {
        "module_id": "TM-URG-01",
        "title": "Recognizing Urgency-Based Phishing",
        "bias_target": "Urgency",
        "duration_seconds": 180,
        "video_urls": [
            "https://www.youtube.com/embed/xBTebn3sNlM",
            "https://www.youtube.com/embed/kWrLi-ETeME",
            "https://www.youtube.com/embed/oXUE3sMOsc4",
        ],
    },
    {
        "module_id": "TM-AUT-01",
        "title": "Spotting Authority-Based Phishing",
        "bias_target": "Authority",
        "duration_seconds": 180,
        "video_urls": [
            "https://www.youtube.com/embed/343eqsob9FE",
            "https://www.youtube.com/embed/OeTKw49qgRY",
            "https://www.youtube.com/embed/yJim30KCZco",
        ],
    },
    {
        "module_id": "TM-SCA-01",
        "title": "Identifying Scarcity-Based Phishing",
        "bias_target": "Scarcity",
        "duration_seconds": 180,
        "video_urls": [
            "https://www.youtube.com/embed/4gj1gJy5Ui8",
            "https://www.youtube.com/embed/5XWQicNOuBs",
            "https://www.youtube.com/embed/fzRy3aI2BMI",
        ],
    },
    {
        "module_id": "TM-SOC-01",
        "title": "Understanding Social Proof Phishing",
        "bias_target": "Social Proof",
        "duration_seconds": 180,
        "video_urls": [
            "https://www.youtube.com/embed/ef2vtrTSGgo",
            "https://www.youtube.com/embed/U0S5GLou0Q8",
            "https://www.youtube.com/embed/PkeypxacADg",
        ],
    },
]

def seed_modules():
    with driver.session() as session:
        for module in TRAINING_MODULES:
            session.run("""
                MERGE (m:TrainingModule {module_id: $module_id})
                SET m.title = $title,
                    m.bias_target = $bias_target,
                    m.duration_seconds = $duration_seconds,
                    m.video_urls = $video_urls,
                    m.content_url = $content_url
            """,
                module_id=module["module_id"],
                title=module["title"],
                bias_target=module["bias_target"],
                duration_seconds=module["duration_seconds"],
                video_urls=module["video_urls"],
                content_url=module["video_urls"][0],
            )
            print(f"[Seed] Upserted {module['module_id']}: {module['title']}")

    print("\n[Seed] All 4 TrainingModule nodes seeded successfully.")
    print("[Seed] Verifying...")
    with driver.session() as session:
        result = session.run("MATCH (m:TrainingModule) RETURN m.module_id AS id, m.title AS title, m.content_url AS url")
        for record in result:
            print(f"  ✅ {record['id']} — {record['title']} — {record['url']}")

if __name__ == "__main__":
    seed_modules()