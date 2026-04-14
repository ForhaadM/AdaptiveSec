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
            "https://youtube.com/shorts/xBTebn3sNlM?feature=share",
            "https://youtube.com/shorts/kWrLi-ETeME?feature=share",
            "https://youtube.com/shorts/oXUE3sMOsc4?feature=share",
        ],
    },
    {
        "module_id": "TM-AUT-01",
        "title": "Spotting Authority-Based Phishing",
        "bias_target": "Authority",
        "duration_seconds": 180,
        "video_urls": [
            "https://youtube.com/shorts/343eqsob9FE?feature=share",
            "https://youtube.com/shorts/OeTKw49qgRY?feature=share",
            "https://youtube.com/shorts/yJim30KCZco?feature=share",
        ],
    },
    {
        "module_id": "TM-SCA-01",
        "title": "Identifying Scarcity-Based Phishing",
        "bias_target": "Scarcity",
        "duration_seconds": 180,
        "video_urls": [
            "https://youtube.com/shorts/4gj1gJy5Ui8?feature=share",
            "https://youtube.com/shorts/5XWQicNOuBs?feature=share",
            "https://youtube.com/shorts/fzRy3aI2BMI?feature=share",
        ],
    },
    {
        "module_id": "TM-SOC-01",
        "title": "Understanding Social Proof Phishing",
        "bias_target": "Social Proof",
        "duration_seconds": 180,
        "video_urls": [
            "https://youtube.com/shorts/ef2vtrTSGgo?feature=share",
            "https://youtube.com/shorts/U0S5GLou0Q8?feature=share",
            "https://youtube.com/shorts/PkeypxacADg?feature=share",
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
        result = session.run("MATCH (m:TrainingModule) RETURN m.module_id AS id, m.title AS title")
        for record in result:
            print(f"  ✅ {record['id']} — {record['title']}")


if __name__ == "__main__":
    seed_modules()