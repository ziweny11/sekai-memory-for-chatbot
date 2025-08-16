import json
import os
from typing import Dict, Any


def load_defaults() -> Dict[str, Any]:
    """Load default configuration values"""
    config_path = os.path.join(os.path.dirname(__file__), "defaults.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading defaults: {e}")
        # Return default values
        return {
            "visibility_defaults": { 
                "WM": "global", 
                "IC": "shared", 
                "C2U": "private" 
            },
            "min_confidence": 0.70,
            "max_fact_length": 140,
            "language": "en"
        }
