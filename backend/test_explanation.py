from ml_pipeline.explanation_generator import ExplanationGenerator

def test():
    gen = ExplanationGenerator()
    
    result = gen.generate(
        user_id="test_user_001",
        cognitive_trigger="Urgency_Bias",
        risk_delta=6,
        page_context="URGENT: Your password expires in 24 hours. Click here to reset it immediately.",
        event_id="event_test_001",
        new_score=56,
        new_training_id="TM-URG-01"
    )
    print("=== Urgency Test ===")
    print(result)
    print()

    # Test Authority trigger
    result = gen.generate(
        user_id="test_user_001",
        cognitive_trigger="Authority_Bias",
        risk_delta=10,
        page_context="IT Department: Verify your credentials to maintain system access.",
        event_id="event_test_002",
        new_score=66,
        new_training_id="TM-AUT-01"
    )
    print("=== Authority Test ===")
    print(result)

if __name__ == "__main__":
    test()