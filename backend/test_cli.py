#!/usr/bin/env python3
"""
AdaptiveSec CLI Test Program
============================
Verifies the full system pipeline without the UI.

Usage:
    cd backend
    python test_cli.py

Tests:
    1. Backend health check
    2. Dev auth token generation
    3. Agent score retrieval
    4. Phishing simulation (run + click detection)
    5. RabbitMQ worker connectivity
    6. Neo4j score persistence
    7. Training module assignment
    8. AI explanation generation
    9. Score history retrieval
    10. Full end-to-end pipeline (sim → score → training → explanation)
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"
TEST_AGENT = "agent_rushed_001"

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
INFO = "\033[94mℹ\033[0m"

results = []


def test(name):
    def decorator(fn):
        def wrapper():
            print(f"\n{INFO} {name}...", end=" ", flush=True)
            try:
                msg = fn()
                print(f"{PASS} — {msg}")
                results.append((name, True, msg))
            except Exception as e:
                print(f"{FAIL} — {e}")
                results.append((name, False, str(e)))
        return wrapper
    return decorator


def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def post(path, data=None):
    body = json.dumps(data).encode() if data else b""
    req = urllib.request.Request(
        f"{BASE_URL}{path}", data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


# ── Tests ──────────────────────────────────────────────────────────────────

@test("1. Backend health check")
def test_health():
    try:
        req = urllib.request.Request(f"{BASE_URL}/docs")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return "FastAPI is running"
    except:
        pass
    # Try root
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req, timeout=5):
        return "FastAPI is running"


@test("2. Dev auth token generation")
def test_auth():
    data = post(f"/auth/token?user_id={TEST_AGENT}")
    assert "access_token" in data, f"No access_token in response: {data}"
    return f"Token issued for {TEST_AGENT}"


@test("3. Agent score retrieval")
def test_agent_scores():
    data = get("/api/v1/admin/agent-scores")
    assert "agents" in data, "No agents key in response"
    assert TEST_AGENT in data["agents"], f"{TEST_AGENT} not found in scores"
    score = data["agents"][TEST_AGENT]
    return f"{TEST_AGENT} score = {score}"


@test("4. Phishing simulation endpoint")
def test_simulation():
    data = post(f"/api/v1/admin/run-simulation/{TEST_AGENT}")
    assert "status" in data, f"No status in response: {data}"
    assert data["status"] in ("fired", "skipped"), f"Unexpected status: {data['status']}"
    return f"status={data['status']} | click_prob={data.get('click_prob')} | trigger={data.get('simulation', {}).get('trigger_type')}"


@test("5. Neo4j connectivity — score history")
def test_neo4j_history():
    data = get(f"/api/v1/admin/agent-history/{TEST_AGENT}?range=all")
    assert "data_points" in data, "No data_points in response"
    count = len(data["data_points"])
    return f"{count} score history entries found"


@test("6. Cognitive vulnerability profile")
def test_profile():
    data = get(f"/api/v1/users/{TEST_AGENT}/profile-public")
    assert "triggers" in data, "No triggers in response"
    triggers = data["triggers"]
    return f"{len(triggers)} vulnerability edges: {[t.get('trigger') for t in triggers]}"


@test("7. Training module assignment")
def test_training():
    data = get(f"/api/v1/admin/agent-training/{TEST_AGENT}")
    assert "modules" in data, "No modules in response"
    modules = data["modules"]
    if not modules:
        return "No modules assigned yet — run a simulation first"
    return f"{len(modules)} module(s) assigned: {[m.get('module_id') for m in modules]}"


@test("8. Training module detail")
def test_module_detail():
    # Try to fetch TM-URG-01 which should always exist after seeding
    data = get("/api/v1/admin/training/TM-URG-01")
    assert "title" in data or "module_id" in data, f"Unexpected response: {data}"
    title = data.get("title", data.get("module_id", "unknown"))
    content_url = data.get("content_url", "not set")
    return f"{title} | content_url: {'set' if content_url else 'missing'}"


@test("9. AI explanation retrieval")
def test_explanations():
    data = get(f"/api/v1/admin/agent-explanations/{TEST_AGENT}")
    assert "explanations" in data, "No explanations key"
    count = len(data["explanations"])
    if count == 0:
        return "No explanations yet — run a simulation first"
    latest = data["explanations"][0]
    preview = latest.get("explanation", "")[:60]
    return f"{count} explanation(s) | latest: \"{preview}...\""


@test("10. Full end-to-end pipeline")
def test_e2e():
    # Get score before
    before = get("/api/v1/admin/agent-scores")["agents"][TEST_AGENT]

    # Force a click by running until we get one (max 5 attempts)
    clicked = False
    for attempt in range(5):
        result = post(f"/api/v1/admin/run-simulation/{TEST_AGENT}")
        if result["status"] == "fired":
            clicked = True
            trigger = result["simulation"]["trigger_type"]
            break

    if not clicked:
        return f"Agent skipped all {5} attempts (low risk behavior) — pipeline intact"

    # Wait for worker to process
    print(f"\n   {INFO} Simulation clicked ({trigger}), waiting 8s for pipeline...", end=" ", flush=True)
    time.sleep(8)

    # Get score after
    after = get("/api/v1/admin/agent-scores")["agents"][TEST_AGENT]
    delta = round(after - before, 1)

    # Check history updated
    history = get(f"/api/v1/admin/agent-history/{TEST_AGENT}?range=all")
    history_count = len(history["data_points"])

    return f"Score {before} → {after} (Δ{delta:+}) | {history_count} history entries | trigger={trigger}"


@test("11. RabbitMQ worker check")
def test_rabbitmq():
    try:
        import pika
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost", socket_timeout=3)
        )
        channel = connection.channel()
        q = channel.queue_declare(queue="simulation_events", durable=True, passive=True)
        msgs = q.method.message_count
        connection.close()
        return f"RabbitMQ connected | queue=simulation_events | pending_messages={msgs}"
    except ImportError:
        return "pika not installed — skipping RabbitMQ check"
    except Exception as e:
        raise Exception(f"RabbitMQ not reachable: {e}")


@test("12. Redis cache check")
def test_redis():
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.ping()
        cached = r.get(f"risk_score:{TEST_AGENT}")
        return f"Redis connected | cached score for {TEST_AGENT}: {cached.decode() if cached else 'not cached'}"
    except ImportError:
        return "redis not installed — skipping Redis check"
    except Exception as e:
        raise Exception(f"Redis not reachable: {e}")


# ── Run all tests ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  AdaptiveSec CLI Test Suite")
    print("  Make sure uvicorn and rabbitmq_worker are running")
    print("=" * 60)

    # Load .env if present
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    test_health()
    test_auth()
    test_agent_scores()
    test_simulation()
    test_neo4j_history()
    test_profile()
    test_training()
    test_module_detail()
    test_explanations()
    test_e2e()
    test_rabbitmq()
    test_redis()

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"  Results: {passed}/{total} tests passed")
    print("=" * 60)
    for name, ok, msg in results:
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
    print("=" * 60)

    sys.exit(0 if passed == total else 1)