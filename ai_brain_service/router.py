from typing import Optional, Dict, Any

# Model Registry
MODELS = [
    {
        "name": "gemini-flash",
        "provider": "google",
        "cost_per_1k_tokens": 0.0001,
        "speed": "fast",
        "capability": "simple",
        "enabled": False  # disabled since no API key yet
    },
    {
        "name": "gpt-4",
        "provider": "openai",
        "cost_per_1k_tokens": 0.03,
        "speed": "slow",
        "capability": "advanced",
        "enabled": False
    },
    {
        "name": "mock-local",
        "provider": "internal",
        "cost_per_1k_tokens": 0.0,
        "speed": "instant",
        "capability": "fallback",
        "enabled": True
    }
]

# Task-to-capability mapping
TASK_CAPABILITY_MAP = {
    "summarization": "simple",
    "translation": "simple",
    "threat_analysis": "advanced",
    "code_generation": "advanced"
}

def route_model(task_type: str, max_budget: Optional[float] = None) -> Dict[str, Any]:
    """
    Returns the best model for the task, considering capability and cost.
    Falls back to mock-local if no suitable model found or budget exceeded.
    """
    required_capability = TASK_CAPABILITY_MAP.get(task_type, "simple")
    
    # Filter enabled models matching capability (excluding fallback)
    candidates = [
        m for m in MODELS
        if m["enabled"] and m["capability"] == required_capability
    ]
    
    # Sort by cost (cheapest first)
    candidates.sort(key=lambda x: x["cost_per_1k_tokens"])
    
    selected = None
    for model in candidates:
        if max_budget is not None and model["cost_per_1k_tokens"] > max_budget:
            continue
        selected = model
        break
    
    if selected is None:
        # Fallback to mock
        selected = next(m for m in MODELS if m["name"] == "mock-local")
    
    return {
        "model_name": selected["name"],
        "provider": selected["provider"],
        "cost_per_1k_tokens": selected["cost_per_1k_tokens"],
        "is_fallback": selected["name"] == "mock-local"
    }

def estimate_cost(model_name: str, token_count: int) -> float:
    """Estimate cost based on token usage."""
    for m in MODELS:
        if m["name"] == model_name:
            return round((token_count / 1000) * m["cost_per_1k_tokens"], 6)
    return 0.0