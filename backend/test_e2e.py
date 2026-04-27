import json
from rabbitmq_worker import process_event
from neo4j_client import get_dominant_cognitive_trigger, test_vulnerable_to_edge

event = {
    "user_id": "agent_urgency_test",
    "url": "http://example.com/login",
    "page_context": "URGENT: Your password expires in 24 hours. Click here to reset it immediately or you will be locked out.",
    "timestamp": "2026-03-10T14:00:00Z",
    "simulation_id": "sim_urgent_1",
    "trigger_type": "phishing"
}

print("Initialize dummy baseline...")
test_vulnerable_to_edge("agent_urgency_test", "Scarcity", 0.5)

print("\nRunning event 1...")
process_event(json.dumps(event))

print("\nRunning event 2...")
process_event(json.dumps(event))

print("\nRunning event 3...")
process_event(json.dumps(event))

print("\nChecking dominant trigger...")
trigger = get_dominant_cognitive_trigger("agent_urgency_test")
print("Dominant trigger:", trigger)
