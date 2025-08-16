import json
import os
from typing import Dict, Any


def load_entity_registry() -> Dict[str, Any]:
    """Load entity registry configuration"""
    config_path = os.path.join(os.path.dirname(__file__), "entity_registry.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading entity registry: {e}")
        # Return default registry
        return {
            "world_id": "world",
            "user_id": "user_123",
            "character_aliases": {
                "Byleth": "byleth",
                "Dimitri": "dimitri",
                "Sylvain": "sylvain",
                "Annette": "annette",
                "Dedue": "dedue",
                "Felix": "felix",
                "Mercedes": "mercedes",
                "Ashe": "ashe"
            }
        }
